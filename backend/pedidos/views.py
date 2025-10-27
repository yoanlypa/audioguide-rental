import logging
import json
from datetime import datetime, timedelta

from django.utils import timezone
from django.db import transaction
from django.db.models import Q  
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Pedido, Empresa, PedidoCrucero, Reminder
from .serializers import (
    PedidoSerializer,
    PedidoOpsSerializer,
    PedidoOpsWriteSerializer,
    EmpresaSerializer,
    PedidoCruceroSerializer,
    ReminderSerializer,
    EmailTokenObtainPairSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView

# ---------------------------------------------------------
# Pedidos "normales"
# ---------------------------------------------------------

class PedidoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista de solo lectura para que cada usuario
    vea SUS pedidos (mis pedidos).
    No permite crear ni modificar pedidos.
    """
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # pedidos visibles solo del usuario autenticado
        user = self.request.user
        return Pedido.objects.filter(user=user).order_by("-fecha_creacion")


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class MisPedidosView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pedidos = Pedido.objects.filter(user=request.user)
        serializer = PedidoSerializer(pedidos, many=True)
        return Response(serializer.data)


class BulkPedidos(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ser = PedidoSerializer(data=request.data, many=True)
        if ser.is_valid():
            ser.save()
            return Response({"created": len(ser.data)})
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------
# Cruceros (bulk)
# ---------------------------------------------------------

class CruceroBulkView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # ---------- GET con ordering flexible ----------
    def get(self, request):
        log = logging.getLogger(__name__)
        ordering_raw = request.query_params.getlist("ordering")
        log.info("ordering param crudo → %s", ordering_raw)

        qs = PedidoCrucero.objects.all()

        if ordering_raw:
            order_fields: list[str] = []
            for item in ordering_raw:
                if isinstance(item, str) and item.startswith("["):
                    try:
                        parsed = json.loads(item)
                    except Exception:
                        parsed = ast.literal_eval(item)
                    if isinstance(parsed, list):
                        order_fields.extend([str(x).strip() for x in parsed if str(x).strip()])
                else:
                    order_fields.extend([p.strip() for p in item.split(",") if p.strip()])

            # quita duplicados conservando orden
            order_fields = [f for f in dict.fromkeys(order_fields) if f]

            if order_fields:
                try:
                    qs = qs.order_by(*order_fields)
                except Exception as e:
                    log.warning("ordering inválido %s → fallback por defecto (%s)", order_fields, e)
                    qs = qs.order_by("-updated_at", "-uploaded_at")
            else:
                qs = qs.order_by("-updated_at", "-uploaded_at")
        else:
            qs = qs.order_by("-updated_at", "-uploaded_at")

        serializer = PedidoCruceroSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ---------- POST con reglas preliminary/final + creación de Pedidos ----------
    def post(self, request):
        payload = request.data

        # Fecha y hora exacta de “impresión” del lote
        printing_dt = timezone.now()

        # Normaliza a rows + meta y fuerza printing_date desde servidor
        if isinstance(payload, dict) and "rows" in payload:
            meta = payload.get("meta", {}) or {}
            rows = payload.get("rows", []) or []

            common_keys = (
                "service_date", "ship", "status", "terminal",
                "supplier", "emergency_contact"
            )

            full_rows = []
            for r in rows:
                rr = dict(r)
                for k in common_keys:
                    v = meta.get(k, None)
                    if v not in (None, ""):
                        rr[k] = v
                rr["printing_date"] = printing_dt  # siempre desde backend
                full_rows.append(rr)
            rows = full_rows
        else:
            meta = {}
            rows = payload if isinstance(payload, list) else []
            rows = [{**r, "printing_date": printing_dt} for r in rows]

        # Valida cruceros
        ser = PedidoCruceroSerializer(data=rows, many=True)
        ser.is_valid(raise_exception=True)
        rows_data = ser.validated_data

        created = overwritten = blocked = 0
        blocked_groups = []
        created_pedidos = 0

        # Agrupar por (fecha, barco)
        groups = {}
        for r in rows_data:
            groups.setdefault((r["service_date"], r["ship"]), []).append(r)

        with transaction.atomic():
            for (service_date, ship), lote in groups.items():
                new_status = (lote[0]["status"] or "").lower()
                qs = PedidoCrucero.objects.filter(service_date=service_date, ship=ship)

                final_exists = qs.filter(status__iexact="final").exists()
                if new_status == "preliminary" and final_exists:
                    blocked += len(lote)
                    blocked_groups.append({"service_date": service_date, "ship": ship})
                    continue

                overwritten += qs.count()
                qs.delete()

                PedidoCrucero.objects.bulk_create([PedidoCrucero(**r) for r in lote])
                created += len(lote)

                # Crear también Pedidos si meta.empresa está presente
                empresa_id = meta.get("empresa")
                if empresa_id:
                    estado_pedido = meta.get("estado_pedido") or "pagado"

                    ped_objs = []
                    for r in lote:
                        kwargs = dict(
                            empresa_id=empresa_id,
                            user=request.user,
                            excursion=r.get("excursion") or "",
                            estado=estado_pedido,
                            # ¡Eliminados: lugar_entrega, lugar_recogida, emisores!
                            fecha_inicio=service_date,
                            fecha_fin=None,
                            pax=r.get("pax") or 0,
                            bono=r.get("sign") or "",
                            guia="",
                            tipo_servicio="crucero",
                            notas="; ".join(
                                x for x in [
                                    f"Barco: {ship}",
                                    f"Idioma: {r.get('language') or ''}",
                                    f"Hora: {r.get('arrival_time') or ''}",
                                    f"Proveedor: {lote[0].get('supplier') or ''}",
                                    f"Terminal: {lote[0].get('terminal') or ''}",
                                    f"Impresión: {printing_dt.isoformat(timespec='minutes')}",
                                ] if x and not x.endswith(': ')
                            ),
                        )
                        ped_objs.append(Pedido(**kwargs))

                    if ped_objs:
                        Pedido.objects.bulk_create(ped_objs)
                        created_pedidos += len(ped_objs)

        return Response(
            {
                "created": created,
                "overwritten": overwritten,
                "blocked": blocked,
                "blocked_groups": blocked_groups,
                "created_pedidos": created_pedidos,
            },
            status=status.HTTP_201_CREATED,
        )
# feedback se guarda en request para que Middleware/Response lo lea
def _add_feedback(request, ship, sd, status, n):
    msg = f"♻️ Sobrescrito {ship} {sd} ({status}) con {n} excursiones nuevas"
    fb = getattr(request, "_feedback", [])
    fb.append(msg)
    setattr(request, "_feedback", fb)


# ---------------------------------------------------------
# API de Operaciones (trabajadores)
# ---------------------------------------------------------

def _parse_dt(value: str):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt
    except Exception:
        return None


class IsAuthenticatedAndOwnerOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return getattr(obj, "user_id", None) == request.user.id


class EmpresaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/empresas/ (staff: todas | no-staff: solo la suya)
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Empresa.objects.all().order_by("nombre")
    serializer_class = EmpresaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.is_staff:
            return qs
        nombre = (getattr(u, "empresa", "") or "").strip()
        return qs.filter(nombre=nombre) if nombre else qs.none()

class PedidoOpsViewSet(viewsets.ModelViewSet):
    """
    Endpoint OFICIAL para crear, editar y gestionar pedidos operativos.

    - GET /api/ops/pedidos/              -> listado filtrable (panel operaciones)
    - POST /api/ops/pedidos/             -> crear pedido
    - PATCH /api/ops/pedidos/{id}/       -> editar pedido parcial
    - POST /api/ops/pedidos/{id}/delivered/ -> marcar entregado
    - POST /api/ops/pedidos/{id}/collected/ -> marcar recogido

    Reglas:
    - perform_create fuerza user=request.user.
    - Serializers:
        * list/retrieve usan PedidoOpsSerializer (lectura).
        * create/update usan PedidoOpsWriteSerializer (escritura).
    - Filtros por fecha, tipo_servicio, estado, empresa, etc.
    """

    permission_classes = [permissions.IsAuthenticated]  # o tu permiso custom IsAuthenticatedAndOwnerOrStaff
    queryset = Pedido.objects.all().order_by("-fecha_creacion")

    def get_serializer_class(self):
        # Para lectura (GET) usamos el serializer de lectura
        if self.action in ["list", "retrieve"]:
            return PedidoOpsSerializer
        # Para escritura (POST, PATCH) usamos el serializer de escritura
        if self.action in ["create", "update", "partial_update"]:
            return PedidoOpsWriteSerializer
        # Para acciones custom tipo delivered/collected, vamos a devolver lectura final
        if self.action in ["delivered", "collected"]:
            return PedidoOpsSerializer
        # fallback seguro
        return PedidoOpsSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Pedido.objects.all()

        # Si NO es staff, solo sus pedidos o de su empresa (dependiendo de tu regla)
        if not user.is_staff:
            # restringimos pedidos visibles
            qs = qs.filter(user=user)

        # filtros query params
        params = self.request.query_params

        # por estado (ej: ?estado=pagado)
        estado = params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)

        # por tipo de servicio (?tipo_servicio=dia_Completo / mediodia / circuito / crucero ...)
        tipo_servicio = params.get("tipo_servicio")
        if tipo_servicio:
            qs = qs.filter(tipo_servicio=tipo_servicio)

        # rango de fechas (?desde=YYYY-MM-DD&hasta=YYYY-MM-DD)
        desde = params.get("desde")
        hasta = params.get("hasta")

        if desde:
            try:
                d = datetime.fromisoformat(desde).date()
                qs = qs.filter(fecha_inicio__gte=d)
            except ValueError:
                pass

        if hasta:
            try:
                h = datetime.fromisoformat(hasta).date()
                qs = qs.filter(fecha_inicio__lte=h)
            except ValueError:
                pass

        # empresa específica (solo staff debería poder filtrar esto)
        empresa_id = params.get("empresa")
        if empresa_id and user.is_staff:
            qs = qs.filter(empresa_id=empresa_id)

        return qs.order_by("-fecha_creacion", "-id")

    def perform_create(self, serializer):
        # SIEMPRE atamos el pedido al usuario autenticado
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def delivered(self, request, pk=None):
        """
        Marcar el pedido como ENTREGADO y registrar cuántos receptores se dejaron realmente.

        Body esperado (JSON):
        {
            "delivered_pax": 32,        # opcional
            "override_pax": true,       # opcional, si quieres que 'pax' pase a ser ese número
            "note": "dejamos 2 extra"   # opcional, comentario libre
        }

        Qué hace:
        - Cambia estado a "entregado"
        - Añade un evento a `updates` con delivered_pax
        - Si override_pax=true, actualiza self.pax
        - Guarda todo
        - Devuelve el pedido actualizado
        """
        pedido = self.get_object()

        delivered_pax = request.data.get("delivered_pax", None)
        override_pax = request.data.get("override_pax", False)
        note = request.data.get("note", None)

        # IMPORTANTE:
        # set_delivered ya se encarga de:
        # - self.estado = "entregado"
        # - loggear delivered_pax y note dentro de updates
        # - si override_pax=True => self.pax = delivered_pax
        # - save(update_fields=["estado", "updates", "pax"])
        pedido.set_delivered(
            user=request.user,
            note=note,
            delivered_pax=delivered_pax,
            override_pax=bool(override_pax),
        )

        serializer = PedidoOpsSerializer(pedido, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def collected(self, request, pk=None):
        """
        Marcar el pedido como RECOGIDO.
        Opcionalmente puedes mandar "note" en el body para guardar en updates.
        {
            "note": "recogido todo ok"
        }
        """
        pedido = self.get_object()
        note = request.data.get("note", None)

        pedido.set_collected(
            user=request.user,
            note=note,
        )

        serializer = PedidoOpsSerializer(pedido, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReminderViewSet(viewsets.ModelViewSet):
    """
    Recordatorios personales del usuario autenticado.
    Permite filtrar por:
      - done=true/false
      - overdue=true (atrasados)
      - q=texto (busca en title / notes)
      - due_before=YYYY-MM-DD
      - due_after=YYYY-MM-DD
    Orden: primero no hechos, luego más urgentes.
    """
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # punto de partida: solo los recordatorios del usuario
        qs = Reminder.objects.filter(user=user)

        params = self.request.query_params

        # done=true / false
        done = params.get("done")
        if done is not None:
            if done.lower() in ("1", "true", "yes", "y"):
                qs = qs.filter(is_done=True)
            elif done.lower() in ("0", "false", "no", "n"):
                qs = qs.filter(is_done=False)

        # overdue=true  => due_at < ahora y is_done=False
        overdue = params.get("overdue")
        if overdue and overdue.lower() in ("1", "true", "yes", "y"):
            qs = qs.filter(is_done=False, due_at__lt=timezone.now())

        # q=texto libre
        query_text = params.get("q")
        if query_text:
            qs = qs.filter(
                Q(title__icontains=query_text) |
                Q(notes__icontains=query_text)
            )

        # due_before / due_after (YYYY-MM-DD)
        due_before = params.get("due_before")
        if due_before:
            try:
                cutoff = datetime.fromisoformat(due_before)
                qs = qs.filter(due_at__lte=cutoff)
            except ValueError:
                pass  # si no es fecha válida, lo ignoramos

        due_after = params.get("due_after")
        if due_after:
            try:
                cutoff = datetime.fromisoformat(due_after)
                qs = qs.filter(due_at__gte=cutoff)
            except ValueError:
                pass

        # Orden final: primero los no hechos, luego por fecha, luego id
        qs = qs.order_by("is_done", "due_at", "id")
        return qs

    @action(detail=True, methods=["post"])
    def done(self, request, pk=None):
        """
        Marcar recordatorio como hecho (is_done=True).
        """
        reminder = self.get_object()
        reminder.is_done = True
        reminder.save(update_fields=["is_done"])
        return Response(self.serializer_class(reminder).data)

# ---------------------------------------------------------
# Perfil simple para el frontend (/api/me/)
# ---------------------------------------------------------
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    """
    Devuelve info del usuario + empresa_id resuelta (si existe).
    """
    u = request.user
    empresa_name = (getattr(u, "empresa", "") or "").strip()
    empresa_id = None
    if empresa_name:
        from .models import Empresa
        empresa_id = Empresa.objects.filter(nombre=empresa_name).values_list("id", flat=True).first()

    return Response({
        "id": u.id,
        "username": getattr(u, "username", ""),
        "email": getattr(u, "email", ""),
        "is_staff": getattr(u, "is_staff", False),
        "empresa_name": empresa_name,
        "empresa_id": empresa_id,
    })
    
    
    
    
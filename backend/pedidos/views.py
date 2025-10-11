# pedidos/views.py
import logging
import json
import ast
from datetime import date, datetime

from django.shortcuts import render
from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, permissions, status, generics, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes

from rest_framework_simplejwt.views import TokenObtainPairView

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Pedido, PedidoCrucero, Empresa, Reminder
from .serializers import (
    PedidoSerializer,
    PedidoCruceroSerializer,
    EmailTokenObtainPairSerializer,
    PedidoOpsSerializer, PedidoOpsWriteSerializer,
    EmpresaSerializer, ReminderSerializer,
)

# ---------------------------------------------------------
# Pedidos "normales"
# ---------------------------------------------------------

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "sede",
                openapi.IN_QUERY,
                description="Filtra por sede",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    def get_queryset(self):
        # Devuelve solo los pedidos del usuario autenticado
        return Pedido.objects.filter(user=self.request.user)


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class MisPedidosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pedidos = Pedido.objects.filter(user=request.user)
        serializer = PedidoSerializer(pedidos, many=True)
        return Response(serializer.data)


class BulkPedidos(APIView):
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

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
        # coherente con el resto del código: campo 'user'
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
    serializer_class = PedidoOpsSerializer
    permission_classes = [IsAuthenticatedAndOwnerOrStaff]
    queryset = Pedido.objects.all().order_by("-fecha_inicio", "-id")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PedidoOpsWriteSerializer
        return PedidoOpsSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # Si no es staff, solo sus pedidos
        user = self.request.user
        if not user.is_staff:
            qs = qs.filter(user=user)

        # Filtro por estado (coma-separado)
        status_param = self.request.query_params.get("status")
        if status_param:
            parts = [p.strip() for p in status_param.split(",") if p.strip()]
            if parts:
                qs = qs.filter(estado__in=parts)

        # Filtro por tipo_servicio (coma-separado)
        ts_param = self.request.query_params.get("tipo_servicio")
        if ts_param:
            ts_parts = [p.strip() for p in ts_param.split(",") if p.strip()]
            if ts_parts:
                qs = qs.filter(tipo_servicio__in=ts_parts)

        # Rango de fechas (acepta ISO con Z)
        date_from = _parse_dt(self.request.query_params.get("date_from"))
        date_to   = _parse_dt(self.request.query_params.get("date_to"))

        if date_from:
            if isinstance(date_from, datetime):
                date_from = date_from.date()
            qs = qs.filter(fecha_inicio__gte=date_from)
        if date_to:
            if isinstance(date_to, datetime):
                date_to = date_to.date()
            qs = qs.filter(fecha_inicio__lte=date_to)

        return qs

    @action(detail=True, methods=["post"])
    def delivered(self, request, pk=None):
        obj = self.get_object()
        delivered_pax = request.data.get("delivered_pax", None)
        override_pax = bool(request.data.get("override_pax", False))
        obj.set_delivered(user=request.user, delivered_pax=delivered_pax, override_pax=override_pax)
        return Response({"ok": True, "status": "entregado", "id": obj.id, "pax": obj.pax})

    @action(detail=True, methods=["post"])
    def collected(self, request, pk=None):
        obj = self.get_object()
        obj.set_collected(user=request.user)
        return Response({"ok": True, "status": "recogido", "id": obj.id})

class ReminderViewSet(viewsets.ModelViewSet):
    """
    GET /api/reminders/?done=true|false&overdue=true|false&q=texto&from=ISO&to=ISO
    """
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    # base: sólo los del usuario autenticado
    queryset = Reminder.objects.all()

    def get_queryset(self):
        qs = Reminder.objects.filter(user=self.request.user)

        # --- filtros opcionales ---
        done = (self.request.query_params.get("done") or "").strip().lower()
        if done in ("true", "1", "yes", "y"):
            qs = qs.filter(is_done=True)
        elif done in ("false", "0", "no", "n"):
            qs = qs.filter(is_done=False)

        overdue = (self.request.query_params.get("overdue") or "").strip().lower()
        if overdue in ("true", "1", "yes", "y"):
            qs = qs.filter(is_done=False, due_at__lt=timezone.now())

        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(note__icontains=q))

        # rangos de fechas (ISO “YYYY-MM-DD” o “YYYY-MM-DDTHH:MM”)
        def _parse_dt(s):
            if not s:
                return None
            try:
                s = s.replace("Z", "+00:00")
                dt = timezone.datetime.fromisoformat(s)
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                return dt
            except Exception:
                return None

        dfrom = _parse_dt(self.request.query_params.get("from"))
        dto   = _parse_dt(self.request.query_params.get("to"))
        if dfrom:
            qs = qs.filter(due_at__gte=dfrom)
        if dto:
            qs = qs.filter(due_at__lte=dto)

        # orden: primero pendientes por fecha, luego hechos
        return qs.order_by("is_done", "due_at", "id")
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
    
    
    
    
import logging
from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics, filters
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Pedido, PedidoCrucero
from .serializers import PedidoSerializer, PedidoCruceroSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
from datetime import date, datetime
import logging, json, ast


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



class CruceroBulkView(APIView):
    permission_classes = [IsAuthenticated]

    # ---------- GET con ordering flexible (tal como tenías) ----------
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

    # ---------- POST con reglas preliminary/final ----------
    
    def post(self, request):
        ser = PedidoCruceroSerializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)
        rows = ser.validated_data

        created = overwritten = blocked = 0
        blocked_groups = []

        # 🔑 Agrupar por barco-fecha (sign ignorado)
        groups: dict[tuple, list] = {}
        for r in rows:
            groups.setdefault((r["service_date"], r["ship"]), []).append(r)

        with transaction.atomic():
            for (service_date, ship), lote in groups.items():
                new_status = lote[0]["status"].lower()           # case-insensitive

                qs = PedidoCrucero.objects.filter(service_date=service_date,
                                                  ship=ship)

                # ¿Hay algún FINAL existente?
                final_exists = qs.filter(status__iexact="final").exists()

                # ─── Regla de control ────────────────────────────
                if new_status == "preliminary" and final_exists:
                    blocked += len(lote)
                    blocked_groups.append(
                        {"service_date": service_date, "ship": ship}
                    )
                    continue  # no tocamos nada

                # Borramos todo lo previo (sea prelim o final)
                overwritten += qs.count()
                qs.delete()

                # Insertamos todo el lote tal cual (permitimos signs duplicados)
                PedidoCrucero.objects.bulk_create(
                    [PedidoCrucero(**r) for r in lote]
                )
                created += len(lote)

        return Response(
            {
                "created": created,
                "overwritten": overwritten,
                "blocked": blocked,
                "blocked_groups": blocked_groups,
            },
            status=status.HTTP_201_CREATED,
        )

# feedback se guarda en una lista en request para que Middleware/Response
def _add_feedback(self, ship, sd, status, n):
    msg = (
        f"♻️ Sobrescrito {ship} {sd} ({status}) "
        f"con {n} excursiones nuevas"
    )
    getattr(self.request, "_feedback", []).append(msg)


from .serializers import PedidoOpsSerializer

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
        return getattr(obj, "usuario_id", None) == request.user.id

class PedidoOpsViewSet(viewsets.ModelViewSet):
    """
    /api/ops/pedidos/ → listado y acciones para trabajadores.
    Staff: ve todos; no staff: solo los suyos (usuario=request.user).
    Filtros (query params):
      - status=pagado,entregado,recogido
      - date_from=ISO
      - date_to=ISO
    """
    serializer_class = PedidoOpsSerializer
    permission_classes = [IsAuthenticatedAndOwnerOrStaff]

    def get_queryset(self):
        qs = Pedido.objects.all().order_by("-fecha_modificacion")
        user = self.request.user
        if not user.is_staff:
            qs = qs.filter(usuario=user)

        status_param = self.request.query_params.get("status")
        if status_param:
            parts = [p.strip() for p in status_param.split(",") if p.strip()]
            if parts:
                qs = qs.filter(estado__in=parts)

        date_from = _parse_dt(self.request.query_params.get("date_from"))
        date_to   = _parse_dt(self.request.query_params.get("date_to"))
        if date_from:
            qs = qs.filter(fecha_inicio__gte=date_from)
        if date_to:
            qs = qs.filter(fecha_inicio__lte=date_to)

        return qs

    @action(detail=True, methods=["post"])
    def delivered(self, request, pk=None):
        obj = self.get_object()
        obj.set_delivered(user=request.user)
        return Response({"ok": True, "status": "entregado", "id": obj.id})

    @action(detail=True, methods=["post"])
    def collected(self, request, pk=None):
        obj = self.get_object()
        obj.set_collected(user=request.user)
        return Response({"ok": True, "status": "recogido", "id": obj.id})

    @api_view(["GET"])
    @permission_classes([permissions.IsAuthenticated])
    def me_view(request):
        u = request.user
        return Response({
            "id": u.id,
            "username": getattr(u, "username", ""),
            "email": getattr(u, "email", ""),
            "is_staff": getattr(u, "is_staff", False),
        })

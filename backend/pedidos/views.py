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
        log.info("ordering param crudo → %s", request.query_params.getlist("ordering"))

        qs = PedidoCrucero.objects.all()
        ordering_raw = request.query_params.getlist("ordering")

        order_fields: list[str] = []
        for item in ordering_raw:
            if isinstance(item, str) and item.startswith("["):
                try:
                    parsed = json.loads(item)
                except Exception:
                    parsed = ast.literal_eval(item)
                if isinstance(parsed, list):
                    order_fields.extend([str(x).strip() for x in parsed])
            else:
                order_fields.extend([p.strip() for p in item.split(",") if p.strip()])

        order_fields = [f for f in dict.fromkeys(order_fields) if f]
        if order_fields:
            qs = qs.order_by(*order_fields)

        serializer = PedidoCruceroSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ---------- POST con reglas preliminary/final ----------
    
    def post(self, request):
        ser = PedidoCruceroSerializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)
        rows = ser.validated_data

        created = overwritten = blocked = 0
        blocked_groups: list[dict] = []

        # 🔑 Agrupamos SOLO por fecha + barco
        grouping: dict[tuple, list] = {}
        for r in rows:
            key = (r["service_date"], r["ship"])
            grouping.setdefault(key, []).append(r)

        with transaction.atomic():
            for (service_date, ship), lote in grouping.items():
                new_status = lote[0]["status"]   # todo el Excel lleva el mismo status

                qs = PedidoCrucero.objects.filter(
                    service_date=service_date, ship=ship
                )

                # ‼️ Regla de bloqueo: existe FINAL y viene PRELIMINARY
                if qs.filter(status="final").exists() and new_status == "preliminary":
                    blocked += len(lote)
                    blocked_groups.append(
                        {"service_date": service_date, "ship": ship}
                    )
                    continue

                # 🗑️ Eliminar todo lo existente (sea preliminary o final)
                overwritten += qs.count()
                qs.delete()

                # 🚀 Insertar filas nuevas
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
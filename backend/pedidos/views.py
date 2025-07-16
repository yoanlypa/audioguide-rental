from django.shortcuts import render
from rest_framework import viewsets, permissions, status          
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

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "sede", openapi.IN_QUERY, description="Filtra por sede", type=openapi.TYPE_STRING
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
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        qs = PedidoCrucero.objects.all()

        # filtros opcionales (query-params)
        sd = request.GET.get("service_date")
        ship = request.GET.get("ship")
        if sd:
            qs = qs.filter(service_date=sd)
        if ship:
            qs = qs.filter(ship=ship)

        ser = PedidoCruceroSerializer(qs, many=True)
        return Response(ser.data)
    def post(self, request):
        if not isinstance(request.data, list):
            return Response(
                {"detail": "Se esperaba una lista JSON."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = PedidoCruceroSerializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)

        objs = [PedidoCrucero(**d) for d in ser.validated_data]

        with transaction.atomic():
            # Django 5+: hace UPSERT basado en la UniqueConstraint
            created = PedidoCrucero.objects.bulk_create(
                objs,
                update_conflicts=True,
                unique_fields=["service_date", "ship", "sign"],
                update_fields=[
                    "printing_date",
                    "excursion",
                    "language",
                    "pax",
                    "arrival_time",
                    "status",
                    "terminal",
                    "supplier",
                    "emergency_contact",
                ],
            )
        return Response(
            {"created": len(created), "updated": len(objs) - len(created)},
            201
        )

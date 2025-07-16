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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Listado de todos los pedidos.
        Soporta filtros por query-params: ?service_date=YYYY-MM-DD&ship=NombreBarco
        """
        qs = PedidoCrucero.objects.all()
        sd   = request.query_params.get("service_date")
        ship = request.query_params.get("ship")
        if sd:
            qs = qs.filter(service_date=sd)
        if ship:
            qs = qs.filter(ship=ship)

        serializer = PedidoCruceroSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Inserción/actualización masiva (upsert).
        Usa bulk_create(update_conflicts=True) o tu lógica actual.
        """
        ser = PedidoCruceroSerializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)

        objs = [PedidoCrucero(**d) for d in ser.validated_data]

        # Ejemplo con Django 5+ UPSERT:
        created = PedidoCrucero.objects.bulk_create(
            objs,
            update_conflicts=True,
            unique_fields=["service_date", "ship", "sign"],
            update_fields=[
                "printing_date", "supplier", "emergency_contact",
                "service_date", "ship", "sign", "excursion",
                "language", "pax", "arrival_time", "status", "terminal",
            ],
        )
        return Response(
                {"created": len(created), "updated": len(objs) - len(created)},
                status=status.HTTP_201_CREATED
            )
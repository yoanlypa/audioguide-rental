from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Pedido
from .serializers import PedidoSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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
    permission_classes = [AllowAny]        
    def post(self, request):
        ser = PedidoSerializer(data=request.data, many=True)
        if ser.is_valid():
            ser.save()
            return Response({"created": len(ser.data)})
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)        

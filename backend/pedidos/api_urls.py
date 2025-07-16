from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PedidoViewSet, BulkPedidos, CruceroBulkView, PedidoCruceroListView

router = DefaultRouter()
router.register(r'pedidos', PedidoViewSet, basename='pedido')

urlpatterns = [
    path('', include(router.urls)),
    path("pedidos/bulk/", BulkPedidos.as_view()),

    path("pedidos/cruceros/bulk/", CruceroBulkView.as_view()),
]

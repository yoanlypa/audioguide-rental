from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PedidoViewSet, BulkPedidos, CruceroBulkView, PedidoOpsViewSet, me_view

router = DefaultRouter()
router.register(r"ops/pedidos", PedidoOpsViewSet, basename="ops-pedidos")

urlpatterns = [
    path('', include(router.urls)),
    path("pedidos/bulk/", BulkPedidos.as_view()),
    path("me/", me_view, name="me"),
    path("pedidos/cruceros/bulk/", CruceroBulkView.as_view()),
]

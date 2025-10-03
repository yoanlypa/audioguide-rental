from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PedidoViewSet, BulkPedidos, CruceroBulkView, PedidoOpsViewSet, me_view

router = DefaultRouter()
# ViewSet normal (si lo usas desde el frontend)
router.register(r"pedidos", PedidoViewSet, basename="pedidos")
# Panel de operaciones (trabajadores)
router.register(r"ops/pedidos", PedidoOpsViewSet, basename="ops-pedidos")

urlpatterns = [
    path('', include(router.urls)),
    path("mis-pedidos/", MisPedidosView.as_view(), name="mis_pedidos"),
    path("pedidos/bulk/", BulkPedidos.as_view(), name="pedidos_bulk"),
    path("pedidos/cruceros/bulk/", CruceroBulkView.as_view()),
    path("me/", me_view, name="me"),
]

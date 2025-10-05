# pedidos/api_urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse

from .views import (
    PedidoViewSet,
    PedidoOpsViewSet,
    MisPedidosView,
    BulkPedidos,
    CruceroBulkView,
    EmpresaViewSet,
    me_view,
)

# Routers para ViewSets
router = DefaultRouter()
router.register(r"pedidos", PedidoViewSet, basename="pedidos")
router.register(r"ops/pedidos", PedidoOpsViewSet, basename="ops-pedidos")
router.register(r"empresas", EmpresaViewSet, basename="empresas")

def empresas_ping(_):
    return JsonResponse({"ok": True, "where": "pedidos.urls/empresas-ping"})
# URL patterns para APIViews y funciones
urlpatterns = [
    path("empresas-ping/", empresas_ping),
    path("mis-pedidos/", MisPedidosView.as_view(), name="mis_pedidos"),
    path("pedidos/bulk/", BulkPedidos.as_view(), name="pedidos_bulk"),
    path("pedidos/cruceros/bulk/", CruceroBulkView.as_view(), name="cruceros_bulk"),
    path("me/", me_view, name="me"),
]

# Importante: añadimos también las rutas del router
urlpatterns += router.urls

from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import PedidoViewSet, PedidoOpsViewSet, EmpresaViewSet, ReminderViewSet, CruceroBulkView, MisPedidosView, me_view

router = DefaultRouter()
router.register(r'pedidos', PedidoViewSet, basename='pedido')
router.register(r'ops/pedidos', PedidoOpsViewSet, basename='pedido-ops')
router.register(r'empresas', EmpresaViewSet, basename='empresa')
router.register(r'reminders', ReminderViewSet, basename='reminder')

urlpatterns = [
    *router.urls,
    path('mis-pedidos/', MisPedidosView.as_view(), name='mis-pedidos'),
    path('pedidos/cruceros/bulk/', CruceroBulkView.as_view(), name='crucero-bulk'),
    path('me/', me_view, name='me'),
]

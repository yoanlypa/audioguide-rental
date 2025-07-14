"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from pedidos.views import EmailTokenObtainPairView, MisPedidosView
from pedidos.api_urls import router
from rest_framework.routers import DefaultRouter
from pedidos.views import PedidoViewSet
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Innovations Tours API",
        default_version="v1",
        description="Alquiler de radioguías",
        terms_of_service="https://innovations-tours.com/terms",
        contact=openapi.Contact(email="dev@innovations-tours.com"),
        license=openapi.License(name="MIT"),
    ),
    public=False,                           # <- Swagger requiere auth
    permission_classes=[permissions.IsAdminUser],
)
router = DefaultRouter()
router.register(r'pedidos', PedidoViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),
        # Endpoints simples de JWT:
    path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/",   schema_view.with_ui("redoc",   cache_timeout=0), name="schema-redoc"),
 
    # endpoints de pedidos
    path('api/', include(router.urls)),
    path("pedidos/bulk/", BulkPedidos.as_view()),
    path('mis-pedidos/', MisPedidosView.as_view()),
]

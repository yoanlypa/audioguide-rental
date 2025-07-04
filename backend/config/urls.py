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

router = DefaultRouter()
router.register(r'pedidos', PedidoViewSet)


urlpatterns = [
    path("admin/", admin.site.urls),
        # Endpoints simples de JWT:
    path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
 
 
    # endpoints de pedidos
    path('api/', include(router.urls)),
    
    path('mis-pedidos/', MisPedidosView.as_view()),
]
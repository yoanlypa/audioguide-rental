from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Importamos tu vista de login personalizada por email
from pedidos.views import EmailTokenObtainPairView

schema_view = get_schema_view(
    openapi.Info(
        title="Appit API",
        default_version="v1",
        description="API documentation for Appit backend",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),

    # Auth (JWT login via email)
    path("api/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Rutas principales de la app (pedidos, empresas, reminders, crucero bulk, mis pedidos, etc.)
    path("api/", include("pedidos.api_urls")),

    # Documentación API
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]

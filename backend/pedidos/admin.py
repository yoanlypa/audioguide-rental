from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import  Empresa
from .models import Pedido, CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'empresa', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('empresa',)}),
    )

admin.site.register(Pedido)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Empresa)

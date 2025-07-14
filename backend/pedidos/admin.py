from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import  Empresa, Pedido, CustomUser, PedidoCrucero 

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'empresa', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('empresa',)}),
    )
class PedidoCruceroAdmin(admin.ModelAdmin):
    list_display  = ("service_date", "ship", "sign", "excursion", "pax")
    list_filter   = ("service_date", "ship")
    search_fields = ("sign", "excursion", "language")
    date_hierarchy = "service_date"

admin.site.register(Pedido)
@admin.register(PedidoCrucero)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Empresa)

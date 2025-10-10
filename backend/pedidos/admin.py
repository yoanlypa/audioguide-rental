from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import  Empresa, Pedido, CustomUser, PedidoCrucero, Reminder

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'empresa', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('empresa',)}),
    )
@admin.register(PedidoCrucero)
class PedidoCruceroAdmin(admin.ModelAdmin):
    list_filter   = ("service_date", "ship")
    search_fields = ("sign", "excursion", "language")
    date_hierarchy = "service_date"
    list_display = (
        'printing_date', 'service_date', 'ship',
        'sign', 'excursion', 'pax', 'status', 'terminal',
    )
    ordering = ['service_date', 'ship', 'sign']
@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "due_at", "done", "created_at")
    list_filter = ("done", "due_at", "user")
    search_fields = ("title", "note", "user__email", "user__username")
    
admin.site.register(Pedido)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Empresa)


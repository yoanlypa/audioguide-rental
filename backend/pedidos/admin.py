from datetime import timezone
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
    list_display = ("id", "title", "due_at", "overdue", "user", "created_at")
    list_select_related = ("user",)
    search_fields = ("title", "note", "user__username", "user__email")
    # Quitamos 'done' porque no existe en el modelo; filtramos por fecha y usuario
    list_filter = ("due_at", "user")
    ordering = ("-due_at", "-id")
    readonly_fields = ("created_at",)

    def overdue(self, obj):
        """Indicador calculado de si está vencido."""
        if not obj.due_at:
            return False
        return obj.due_at < timezone.now()

    overdue.boolean = True
    overdue.short_description = "Vencido"
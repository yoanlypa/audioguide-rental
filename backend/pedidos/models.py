from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractUser



class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    empresa = models.CharField(max_length=255)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # solo username se pedirá al crear desde la terminal

    def __str__(self):
        return f"{self.username} ({self.empresa})"

class Empresa(models.Model):
        nombre = models.CharField(max_length=100)

        def __str__(self):
            return self.nombre
        
class Pedido(models.Model):
        user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)    
        empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pedidos')
        fecha_creacion = models.DateTimeField(auto_now_add=True)
        excursion = models.CharField(max_length=150, blank=True)
        fecha_inicio = models.DateField()
        fecha_fin = models.DateField(blank=True, null=True)
        ESTADOS = [
            ('pendiente_pago', 'Pendiente de pago'),
            ('pagado',        'Pagado'),
            ('aprobado',      'Aprobado'),
            ('entregado',     'Entregado'),
            ('recogido',      'Recogido'),
        ]
        TIPO_CHOICES = [
        ("mediodia",  "Medio día"),
        ("dia_Completo",  "Día completo"),
        ("circuito",  "Circuito"),
        ("crucero",   "Crucero"),     
    ]

        tipo_servicio = models.CharField(max_length=15, choices=TIPO_CHOICES, default="mediodia")
        estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente_pago')
        lugar_entrega = models.CharField(max_length=150, blank=True)
        lugar_recogida = models.CharField(max_length=150, blank=True)
        notas = models.TextField(blank=True)
        bono = models.CharField(max_length=100, blank=True)
        emisores = models.PositiveIntegerField()
        pax = models.PositiveIntegerField()
        guia = models.CharField(max_length=150, blank=True)
        updates = models.JSONField(default=list, blank=True, editable=False)

        
        
        def save(self, *args, **kwargs):
            if self.pk:
                self.updates.append(now().isoformat())
            super().save(*args, **kwargs)

           # --- helpers internos ---
        def _log_update(self, event, user=None, note=None):
            """Registrar un evento en 'updates'."""
            entry = {
                "ts": timezone.now().isoformat(),  # ISO 8601
                "event": str(event),
            }
            if user:
                entry["user_id"] = user.pk
                entry["user"] = getattr(user, "username", "") or getattr(user, "email", "")
            if note:
                entry["note"] = str(note)
            self.updates = (self.updates or []) + [entry]
    
        # --- helpers de estado ---
        def set_delivered(self, user=None, note=None):
            self.estado = "entregado"
            self.entregado = True
            self._log_update("delivered", user=user, note=note)
            self.save(update_fields=["estado", "entregado", "updates", "fecha_modificacion"])
    
        def set_collected(self, user=None, note=None):
            self.estado = "recogido"
            self.recogido = True
            self._log_update("collected", user=user, note=note)
            self.save(update_fields=["estado", "recogido", "updates", "fecha_modificacion"])
    
        # --- override save para inicializar 'updates' al crear ---
        def save(self, *args, **kwargs):
            is_new = self.pk is None
            if is_new and not self.updates:
                self.updates = [{"ts": timezone.now().isoformat(), "event": "created"}]
            super().save(*args, **kwargs)

class PedidoCrucero(models.Model):
    printing_date      = models.DateField()
    supplier           = models.CharField(max_length=200)
    emergency_contact  = models.CharField(max_length=100, blank=True)
    service_date       = models.DateField()
    ship               = models.CharField(max_length=100)

    sign         = models.CharField(max_length=20)          # nº bus
    excursion    = models.CharField(max_length=200)
    language     = models.CharField(max_length=50, blank=True)
    pax          = models.PositiveIntegerField()
    arrival_time = models.TimeField(null=True, blank=True)

    status   = models.CharField(max_length=20)              # preliminary / final
    terminal = models.CharField(max_length=50, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["service_date", "ship"], name="idx_ship_date"),
        ]
        ordering = ["-updated_at", "-uploaded_at"]
        
    def __str__(self):
        return f"{self.service_date} - {self.ship} - {self.status}"

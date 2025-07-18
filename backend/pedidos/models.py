from django.db import models
from django.utils.timezone import now
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
        updates = models.JSONField(default=list)
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
        
        
        def save(self, *args, **kwargs):
            if self.pk:
                self.updates.append(now().isoformat())
            super().save(*args, **kwargs)

class PedidoCrucero(models.Model):
    # --- metadatos (se repiten en cada fila importada) ---
    printing_date      = models.DateField()
    supplier           = models.CharField(max_length=200)
    emergency_contact  = models.CharField(max_length=100, blank=True)
    service_date       = models.DateField()
    ship               = models.CharField(max_length=100)
    status             = models.CharField(max_length=20, blank=True)   # preliminary / final
    terminal           = models.CharField(max_length=50, blank=True)

    # --- datos de cada maleta ---
    sign               = models.CharField(max_length=20)
    excursion          = models.CharField(max_length=200)
    language           = models.CharField(max_length=50, blank=True)
    pax                = models.PositiveIntegerField()
    arrival_time       = models.TimeField(null=True, blank=True)
    uploaded_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['service_date', 'ship', 'sign']
        verbose_name = "Pedido Crucero"
        verbose_name_plural = "Pedidos Cruceros"
        # Asegura que no se repitan los mismos datos de servicio
        unique_together = ('service_date', 'ship', 'sign', 'status')

        
    def __str__(self):
        return f"{self.service_date} - {self.ship} - {self.sign} - {self.status}"

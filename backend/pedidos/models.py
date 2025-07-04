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


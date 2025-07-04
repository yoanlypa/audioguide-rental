from django.contrib.auth import get_user_model
from .models import Empresa, Pedido
from django.utils import timezone
from django.test import TestCase


class PedidoModelTest(TestCase):
    def test_pedido_str(self):
        empresa = Empresa.objects.create(nombre="Acme")
        user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="pass",
            empresa="Acme",
        )
        pedido = Pedido.objects.create(
            user=user,
            empresa=empresa,
            fecha_inicio=timezone.now().date(),
            emisores=1,
            pax=1,
        )
        self.assertIn("Pedido", str(pedido))

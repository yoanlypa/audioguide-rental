# pedidos/migrations/0012_printing_date_datetime.py
from django.db import migrations, models
import django.utils.timezone

def backfill_printing_dt(apps, schema_editor):
    PedidoCrucero = apps.get_model("pedidos", "PedidoCrucero")
    now = django.utils.timezone.now()
    PedidoCrucero.objects.filter(printing_date__isnull=True).update(printing_date=now)

class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0011_alter_pedidocrucero_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pedidocrucero",
            name="printing_date",
            field=models.DateTimeField(null=True, blank=True),  # paso intermedio
        ),
        migrations.RunPython(backfill_printing_dt, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="pedidocrucero",
            name="printing_date",
            field=models.DateTimeField(default=django.utils.timezone.now),  # ya no null
        ),
    ]

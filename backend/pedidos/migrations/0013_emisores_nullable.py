# pedidos/migrations/0013_emisores_nullable.py
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0012_printing_date_datetime"),  # ajusta si tu último número es otro
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE pedidos_pedido ALTER COLUMN emisores DROP NOT NULL;",
            reverse_sql="ALTER TABLE pedidos_pedido ALTER COLUMN emisores SET NOT NULL;",
        ),
    ]

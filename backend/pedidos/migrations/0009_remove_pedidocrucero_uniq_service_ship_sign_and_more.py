from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0008_uniq_service_ship_sign"),  # la última OK
    ]

    operations = [
        # Solo SQL en la DB (por si el constraint siguiera allí)
        migrations.RunSQL(
            "ALTER TABLE pedidos_pedidocrucero "
            "DROP CONSTRAINT IF EXISTS uniq_service_ship_sign;"
        ),
        # Índice normal NO único
        migrations.AddIndex(
            model_name="pedidocrucero",
            index=models.Index(
                fields=["service_date", "ship"],
                name="idx_ship_date",
            ),
        ),
    ]

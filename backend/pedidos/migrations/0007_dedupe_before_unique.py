from django.db import migrations, transaction, models
from django.db.models import Count, Case, When, Value, IntegerField


def deduplicate(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "PedidoCrucero")

    with transaction.atomic():
        dups = (
            Pedido.objects
            .values("service_date", "ship", "sign")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )

        for d in dups:
            qs = (
                Pedido.objects
                .filter(
                    service_date=d["service_date"],
                    ship=d["ship"],
                    sign=d["sign"],
                )
                .annotate(
                    final_first=Case(
                        When(status="final", then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )
                .order_by("final_first", "-printing_date", "-id")
            )
            keep = qs.first()              # conserva uno
            qs.exclude(id=keep.id).delete()  # borra el resto


class Migration(migrations.Migration):

    dependencies = [
        ("pedidos", "0006_alter_pedidocrucero_unique_together"),
    ]

    operations = [
        migrations.RunPython(deduplicate, migrations.RunPython.noop),
    ]

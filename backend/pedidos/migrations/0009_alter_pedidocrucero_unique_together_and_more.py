from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0008_uniq_service_ship_sign"),   # NO cambies esto
    ]

    operations = [
        # 1️⃣  Borra en BD, **solo si** aún quedara el constraint antiguo
        migrations.RunSQL(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uniq_service_ship_sign'
                       OR conname LIKE '%service_date_ship_sign_status_key'
                ) THEN
                    ALTER TABLE pedidos_pedidocrucero
                    DROP CONSTRAINT IF EXISTS uniq_service_ship_sign;
                END IF;
            END$$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),

        # 2️⃣  Añade (o mantiene) índice NO único para acelerar consultas
        migrations.AddIndex(
            model_name="pedidocrucero",
            index=models.Index(
                fields=["service_date", "ship"],
                name="idx_ship_date",
            ),
        ),

        # 3️⃣  NO hay AlterUniqueTogether ni RemoveConstraint
        #     (así evitamos el ValueError)
    ]

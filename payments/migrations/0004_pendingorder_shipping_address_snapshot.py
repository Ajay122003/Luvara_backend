from django.db import migrations, models


def populate_pending_order_address_snapshots(apps, schema_editor):
    Address = apps.get_model("addresses", "Address")
    PendingOrder = apps.get_model("payments", "PendingOrder")
    database = schema_editor.connection.alias

    for pending in PendingOrder.objects.using(database).all().iterator():
        if not pending.address_id:
            continue

        address = Address.objects.using(database).filter(pk=pending.address_id).first()
        if not address:
            continue

        PendingOrder.objects.using(database).filter(pk=pending.pk).update(
            shipping_address_snapshot={
                "shipping_name": address.name or "",
                "shipping_phone": address.phone or "",
                "shipping_full_address": address.full_address or "",
                "shipping_city": address.city or "",
                "shipping_state": address.state or "",
                "shipping_pincode": address.pincode or "",
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ("addresses", "0001_initial"),
        ("payments", "0003_pendingorder_address_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="pendingorder",
            name="shipping_address_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(
            populate_pending_order_address_snapshots,
            migrations.RunPython.noop,
        ),
    ]
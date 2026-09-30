from django.db import migrations, models


def populate_order_shipping_address_snapshots(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    database = schema_editor.connection.alias

    for order in (
        Order.objects.using(database)
        .filter(address__isnull=False)
        .select_related("address")
        .iterator()
    ):
        address = order.address
        Order.objects.using(database).filter(pk=order.pk).update(
            shipping_name=address.name or "",
            shipping_phone=address.phone or "",
            shipping_full_address=address.full_address or "",
            shipping_city=address.city or "",
            shipping_state=address.state or "",
            shipping_pincode=address.pincode or "",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("addresses", "0001_initial"),
        ("orders", "0009_orderitem_product_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="shipping_name",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_phone",
            field=models.CharField(blank=True, default="", max_length=15),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_full_address",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_city",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_state",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="order",
            name="shipping_pincode",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.RunPython(
            populate_order_shipping_address_snapshots,
            migrations.RunPython.noop,
        ),
    ]
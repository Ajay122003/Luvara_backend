from django.db import migrations, models


def populate_order_item_snapshots(apps, schema_editor):
    OrderItem = apps.get_model("orders", "OrderItem")
    Product = apps.get_model("products", "Product")
    ProductImage = apps.get_model("products", "ProductImage")
    ProductVariant = apps.get_model("products", "ProductVariant")
    database = schema_editor.connection.alias

    for item in OrderItem.objects.using(database).all().iterator():
        if not item.variant_id:
            continue

        variant = (
            ProductVariant.objects.using(database)
            .filter(pk=item.variant_id)
            .first()
        )
        if not variant:
            continue

        product = (
            Product.objects.using(database)
            .filter(pk=variant.product_id)
            .first()
        )
        if not product:
            continue

        updates = {}
        if not item.product_name:
            updates["product_name"] = product.name
        if not item.size:
            updates["size"] = variant.size
        if not item.product_image:
            image = (
                ProductImage.objects.using(database)
                .filter(product_id=product.pk)
                .order_by("pk")
                .first()
            )
            if image and image.image:
                try:
                    updates["product_image"] = image.image.url
                except Exception:
                    pass

        if updates:
            OrderItem.objects.using(database).filter(pk=item.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0008_order_cf_order_id"),
        ("products", "0005_alter_product_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="product_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="product_image",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="orderitem",
            name="size",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.RunPython(
            populate_order_item_snapshots,
            migrations.RunPython.noop,
        ),
    ]
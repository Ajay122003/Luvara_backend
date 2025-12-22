from django.db import models
from categories.models import Category
from product_collections.models import Collection  

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    collections = models.ManyToManyField(
        Collection,
        related_name="products",
        blank=True
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    colors = models.JSONField(default=list)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_effective_price(self):
        return self.sale_price or self.price

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )
    color = models.CharField(max_length=30)
    size = models.CharField(max_length=10)   # S, M, L, XL
    stock = models.PositiveIntegerField()
    

    class Meta:
        unique_together = ("product", "size","color")

    def __str__(self):
        return f"{self.product.name} - {self.size}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images"
    )
    image = models.ImageField(upload_to="products/")

    def __str__(self):
        return f"Image for {self.product.name}"

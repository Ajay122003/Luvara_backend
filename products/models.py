from django.db import models
from categories.models import Category
from product_collections.models import Collection  
from offers.models import Offer
from django.utils import timezone
from decimal import Decimal

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
    
    offer = models.ForeignKey(
        Offer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )
    name = models.CharField(max_length=255)

    sku = models.CharField(max_length=50, unique=True,null=True,blank=True,help_text="Unique Product Number / SKU" )
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
        now = timezone.now()

        # 1️⃣ OFFER PRICE
        if (
            self.offer
            and self.offer.is_active
            and self.offer.start_date <= now
            and self.offer.end_date >= now
        ):
            if self.offer.discount_type == "PERCENT":
                discount = (
                    Decimal(self.offer.discount_value) / Decimal("100")
                ) * self.price
                return (self.price - discount).quantize(Decimal("0.01"))

            if self.offer.discount_type == "FLAT":
                return max(
                    (self.price - Decimal(self.offer.discount_value))
                    .quantize(Decimal("0.01")),
                    Decimal("0.00")
                )

        # 2️⃣ SALE PRICE
        if self.sale_price:
            return self.sale_price.quantize(Decimal("0.01"))

        # 3️⃣ NORMAL PRICE
        return self.price.quantize(Decimal("0.01"))



class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )
    color = models.CharField( max_length=30, blank=True, null=True)
    size = models.CharField(max_length=10)   # S, M, L, XL
    stock = models.PositiveIntegerField()
    

    class Meta:
        # unique only when color exists
        constraints = [
            models.UniqueConstraint(
                fields=["product", "size", "color"],
                name="unique_variant_with_color"
            )
        ]

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

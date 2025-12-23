from django.db import models

DISCOUNT_TYPE_CHOICES = (
    ("PERCENT", "Percentage"),
    ("FLAT", "Flat Amount"),
)

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)

    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES
    )
    discount_value = models.FloatField()

    min_purchase = models.FloatField(default=0)
    max_discount = models.FloatField(null=True, blank=True)  # ⭐ optional cap

    expiry_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    usage_limit = models.IntegerField(default=999999)
    used_count = models.IntegerField(default=0)

    def __str__(self):
        return self.code

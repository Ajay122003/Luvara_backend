from django.db import models
from users.models import User
from products.models import Product

class WishlistItem(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_items"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wishlisted_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")  # same product only once

    def __str__(self):
        return f"{self.user.email} → {self.product.name}"

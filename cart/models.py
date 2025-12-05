from django.db import models
from users.models import User
from products.models import Product

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    quantity = models.IntegerField(default=1)
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=20, blank=True)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product", "size", "color")  # same product can't repeat

    def __str__(self):
        return f"{self.user.email} - {self.product.name}"

from django.db import models
from users.models import User
from addresses.models import Address
from products.models import Product

ORDER_STATUS = [
    ("PENDING", "Pending"),
    ("PROCESSING", "Processing"),
    ("PACKED", "Packed"),
    ("SHIPPED", "Shipped"),
    ("OUT_FOR_DELIVERY", "Out for Delivery"),
    ("DELIVERED", "Delivered"),
    ("CANCELLED", "Cancelled"),
]

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)

    order_number = models.CharField(max_length=20, unique=True)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default="PENDING")  # PAID / FAILED / PENDING
    payment_id = models.CharField(max_length=100, blank=True, null=True) # Razorpay Payment ID

    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # price at purchase time
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.product} - {self.quantity}"


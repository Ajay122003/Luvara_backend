from django.db import models
from users.models import User
from addresses.models import Address
from products.models import Product
from coupons.models import Coupon

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

    # NOTE: Here total_amount = FINAL amount (after discount)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_status = models.CharField(
        max_length=20, default="PENDING"
    )  # PAID / FAILED / PENDING / COD
    payment_id = models.CharField(
        max_length=100, blank=True, null=True
    )  # Razorpay Payment ID

    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)

    quantity = models.IntegerField(default=1)
    price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # price snapshot at purchase
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.product} - {self.quantity}"


RETURN_STATUS = [
    ("REQUESTED", "Requested"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
]


class ReturnRequest(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="returns"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(
        max_length=20, choices=RETURN_STATUS, default="REQUESTED"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return {self.order.order_number} - {self.status}"


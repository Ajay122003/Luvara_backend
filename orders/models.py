from django.db import models
from users.models import User
from addresses.models import Address
from products.models import Product , ProductVariant
from coupons.models import Coupon


def build_shipping_address_snapshot(address):
    return {
        "shipping_name": address.name if address else "",
        "shipping_phone": address.phone if address else "",
        "shipping_full_address": address.full_address if address else "",
        "shipping_city": address.city if address else "",
        "shipping_state": address.state if address else "",
        "shipping_pincode": address.pincode if address else "",
    }


ORDER_STATUS = [
    ("PENDING", "Pending"),
    ("PROCESSING", "Processing"),
    ("PACKED", "Packed"),
    ("SHIPPED", "Shipped"),
    ("OUT_FOR_DELIVERY", "Out for Delivery"),
    ("DELIVERED", "Delivered"),
    ("CANCELLED", "Cancelled"),
]

# Order model

PAYMENT_STATUS = [
    ("COD_PENDING", "Cash on Delivery"),
    ("PENDING", "Payment Pending"),
    ("PAID", "Paid"),
    ("FAILED", "Failed"),
]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    shipping_name = models.CharField(max_length=100, blank=True, default="")
    shipping_phone = models.CharField(max_length=15, blank=True, default="")
    shipping_full_address = models.TextField(blank=True, default="")
    shipping_city = models.CharField(max_length=100, blank=True, default="")
    shipping_state = models.CharField(max_length=100, blank=True, default="")
    shipping_pincode = models.CharField(max_length=10, blank=True, default="")
    total_quantity = models.PositiveIntegerField(default=0)

    order_number = models.CharField(max_length=20, unique=True)

    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)

    payment_status = models.CharField(
    max_length=20,
    choices=PAYMENT_STATUS,   
    default="PENDING"
)

    payment_id = models.CharField(max_length=100, blank=True, null=True)
    cf_order_id = models.CharField(max_length=100, blank=True, null=True)
    cf_payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_method = models.CharField(
    max_length=10,
    choices=[("COD", "COD"), ("ONLINE", "ONLINE")],
    default="COD"
)


    #  ADD THESE TWO
    courier_name = models.CharField(
        max_length=100, blank=True, null=True
    )
    tracking_id = models.CharField(
        max_length=100, blank=True, null=True
    )

    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="PENDING")
    is_admin_viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"

    def get_shipping_address_snapshot(self):
        if not any((
            self.shipping_name,
            self.shipping_phone,
            self.shipping_full_address,
            self.shipping_city,
            self.shipping_state,
            self.shipping_pincode,
        )):
            return None

        return {
            "name": self.shipping_name,
            "phone": self.shipping_phone,
            "full_address": self.shipping_full_address,
            "city": self.shipping_city,
            "state": self.shipping_state,
            "pincode": self.shipping_pincode,
        }



class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True
    )

    product_name = models.CharField(max_length=255, blank=True, default="")
    product_image = models.TextField(blank=True, default="")
    size = models.CharField(max_length=10, blank=True, default="")

    quantity = models.PositiveIntegerField(default=1)
    

    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )  # final price after offer/sale

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    #  DISCOUNT DETAILS
    discount_percent = models.PositiveIntegerField(default=0)
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    offer_title = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # price snapshot at purchase

    color = models.CharField(max_length=20, blank=True)

    def __str__(self):
        if self.variant:
            return f"{self.variant.product.name} ({self.variant.size}) x {self.quantity}"
        return f"Item x {self.quantity}"


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

    status = models.CharField(max_length=20, choices=RETURN_STATUS, default="REQUESTED")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return {self.order.order_number} - {self.status}"

from django.db import models
from django.utils.timezone import now
from datetime import timedelta
from users.models import User


from django.db import models

class SiteSettings(models.Model):
    enable_cod = models.BooleanField(default=True)

    #  SHIPPING SETTINGS (NEW)
    shipping_charge = models.DecimalField( max_digits=10, decimal_places=2, default=0 )
    free_shipping_min_amount = models.DecimalField( max_digits=10, decimal_places=2, default=0 )

    allow_order_cancel = models.BooleanField(default=True)
    allow_order_return = models.BooleanField(default=True)

    def __str__(self):
        return "Site Settings"



class AdminOTP(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        get_latest_by = "created_at"

    def is_expired(self):
        return now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.admin.email}"

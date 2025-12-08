from django.db import models

class SiteSettings(models.Model):
    enable_cod = models.BooleanField(default=True)
    allow_order_cancel = models.BooleanField(default=True)
    allow_order_return = models.BooleanField(default=True)

    def __str__(self):
        return "Ecommerce Site Settings"


from django.db import models
from users.models import User
from django.utils.timezone import now, timedelta

class AdminOTP(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return f"OTP for {self.admin.email}"

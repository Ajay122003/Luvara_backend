from django.db import models
from users.models import User

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)

    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    full_address = models.TextField()

    is_default = models.BooleanField(default=False)
    is_temporary = models.BooleanField(default=False)  # 🔥 important

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.pincode}"



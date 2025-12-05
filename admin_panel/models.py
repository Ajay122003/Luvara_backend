from django.db import models

class SiteSettings(models.Model):
    enable_cod = models.BooleanField(default=True)
    allow_order_cancel = models.BooleanField(default=True)
    allow_order_return = models.BooleanField(default=True)

    def __str__(self):
        return "Ecommerce Site Settings"

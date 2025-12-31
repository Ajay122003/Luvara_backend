from django.db import models
from django.utils.text import slugify

class Offer(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("PERCENT", "Percent"),
        ("FLAT", "Flat Amount"),
    )

    title = models.CharField(max_length=100, unique=True, default="Default Offer")
    slug = models.SlugField(unique=True, blank=True)

    description = models.TextField(blank=True)

    discount_type = models.CharField(
    max_length=10,
    choices=DISCOUNT_TYPE_CHOICES,
    default="PERCENT"
)

    discount_value = models.DecimalField(max_digits=6, decimal_places=2 ,default=0)

    image = models.ImageField(upload_to="offer_images/", blank=True, null=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title



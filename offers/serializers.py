from rest_framework import serializers
from .models import Offer
from django.utils import timezone

class OfferSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    is_valid_now = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "discount_type",
            "discount_value",
            "image",
            "image_url",
            "start_date",
            "end_date",
            "is_active",
            "is_valid_now",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_is_valid_now(self, obj):
        now = timezone.now()
        return (
            obj.is_active
            and obj.start_date <= now
            and obj.end_date >= now
        )

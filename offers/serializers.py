from rest_framework import serializers
from django.utils import timezone
from .models import Offer
from products.serializers import ProductSerializer

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

    # -----------------------------
    # IMAGE URL (SAFE)
    # -----------------------------
    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    # -----------------------------
    # OFFER VALIDITY (STRICT DEADLINE)
    # -----------------------------
    def get_is_valid_now(self, obj):
        now = timezone.now()
        return (
            obj.is_active
            and obj.start_date <= now
            and obj.end_date > now   # 🔥 STRICT CHECK
        )




class OfferDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    # 🔥 THIS IS THE KEY LINE
    products = ProductSerializer(
        many=True,
        read_only=True,
       
    )

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
            "products",          # 🔥 INCLUDED
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
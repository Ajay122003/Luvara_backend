from rest_framework import serializers
from .models import WishlistItem
from products.serializers import ProductSerializer


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(source="product.id", read_only=True)

    class Meta:
        model = WishlistItem
        fields = [
            "id",
            "product_id",
            "product",
            "created_at",
        ]

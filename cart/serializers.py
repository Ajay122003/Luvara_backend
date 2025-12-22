from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductSerializer
from products.models import ProductVariant


class ProductVariantSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "size",
            "stock",
            "product",
        ]


class CartItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant",
            "quantity",
            "total_price",
        ]

    def get_total_price(self, obj):
        product = obj.variant.product
        price = product.sale_price or product.price
        return price * obj.quantity

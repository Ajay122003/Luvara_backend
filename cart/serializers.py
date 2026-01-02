from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductSerializer
from products.models import ProductVariant
from decimal import Decimal

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

    unit_price = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    offer_title = serializers.SerializerMethodField()
    offer_discount = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant",
            "quantity",

            "unit_price",        # 🔥 final offer price
            "original_price",    # 🔥 original price
            "total_price",

            "offer_title",       # 🔥 offer details
            "offer_discount",
        ]

    def get_unit_price(self, obj):
        return str(obj.variant.product.get_effective_price())

    def get_original_price(self, obj):
        product = obj.variant.product
        return str(product.price)

    def get_total_price(self, obj):
        price = obj.variant.product.get_effective_price()
        return str(price * obj.quantity)

    def get_offer_title(self, obj):
        product = obj.variant.product
        if product.offer and product.offer.is_active:
            return product.offer.title
        return None

    def get_offer_discount(self, obj):
        product = obj.variant.product
        if product.offer and product.offer.is_active:
            if product.offer.discount_type == "PERCENT":
                return f"{product.offer.discount_value}% OFF"
            return f"₹{product.offer.discount_value} OFF"
        return None

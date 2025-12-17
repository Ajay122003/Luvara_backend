from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductSerializer


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "size",
            "color",
            "total_price",
        ]

    def get_total_price(self, obj):
        price = obj.product.sale_price or obj.product.price
        return price * obj.quantity
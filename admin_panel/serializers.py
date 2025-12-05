from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import User
from products.models import Product, ProductImage
from products.serializers import ProductSerializer
from rest_framework import serializers
from orders.models import Order, OrderItem
from orders.serializers import OrderDetailSerializer


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data["email"]
        password = data["password"]

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        if not user.is_staff:
            raise serializers.ValidationError("You are not authorized as admin")

        return user
    


class AdminProductCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            "name", "description", "price", "sale_price", "sizes", "colors",
            "stock", "category", "is_active", "images"
        ]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        product = Product.objects.create(**validated_data)

        for img in images:
            ProductImage.objects.create(product=product, image=img)

        return product



class AdminOrderListSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user_email",
            "total_amount",
            "payment_status",
            "status",
            "created_at",
        ]


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user_email",
            "total_amount",
            "payment_status",
            "status",
            "created_at",
            "address",
            "items"
        ]

    def get_items(self, obj):
        return [
            {
                "product": item.product.name if item.product else None,
                "quantity": item.quantity,
                "price": item.price,
                "size": item.size,
                "color": item.color,
            }
            for item in obj.items.all()
        ]

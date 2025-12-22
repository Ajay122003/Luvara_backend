

from rest_framework import serializers
from django.contrib.auth import authenticate
from product_collections.models import Collection
from users.models import User
from products.models import Product, ProductImage, ProductVariant
from orders.models import Order, OrderItem
from addresses.serializers import AddressSerializer
from .models import SiteSettings


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

    collections = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "sale_price",
            "category",
            "collections",
            "is_active",
            "images",
        ]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        collections = validated_data.pop("collections", [])

        product = Product.objects.create(**validated_data)

        if collections:
            product.collections.set(collections)

        for img in images:
            ProductImage.objects.create(product=product, image=img)

        return product
    
    def update(self, instance, validated_data):
        images = validated_data.pop("images", None)
        collections = validated_data.pop("collections", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if collections is not None:
            instance.collections.set(collections)

        if images is not None:
            ProductImage.objects.filter(product=instance).delete()
            for img in images:
                ProductImage.objects.create(product=instance, image=img)

        return instance

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
    address_details = serializers.SerializerMethodField()

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
            "address_details",
            "items",
        ]

    def get_items(self, obj):
        return [
            {
                "product": item.variant.product.name if item.variant else None,
                "size": item.variant.size if item.variant else None,
                "quantity": item.quantity,
                "price": item.price,
            }
            for item in obj.items.all()
        ]


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
          "enable_cod",
          "allow_order_cancel",
          "allow_order_return",
          "shipping_charge",
          "free_shipping_min_amount"
        ]



class AdminEmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already taken")
        return value


class AdminPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=10)

    def validate(self, data):
        user = self.context["request"].user
        if not user.check_password(data["old_password"]):
            raise serializers.ValidationError(
                {"old_password": "Incorrect old password"}
            )
        return data


class AdminOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
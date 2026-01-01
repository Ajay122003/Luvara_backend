
from rest_framework import serializers
from django.contrib.auth import authenticate
from product_collections.models import Collection
from users.models import User
from products.models import Product, ProductImage, ProductVariant
from products.serializers import ProductSerializer
from orders.models import Order, OrderItem
from addresses.serializers import AddressSerializer
from .models import SiteSettings
from django.utils import timezone
from coupons.models import Coupon
from offers.models import Offer
from django.utils.dateparse import parse_datetime


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

class AdminForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        if not User.objects.filter(email=email, is_staff=True).exists():
            raise serializers.ValidationError("Admin not found")
        return email
    
class AdminResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField(min_length=6)




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

    offer = serializers.PrimaryKeyRelatedField(
        queryset=Offer.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "sku", 
            "description",
            "price",
            "sale_price",
            "category",
            "offer", 
            "collections",
            "is_active",
            "images",
        ]
    
    def validate(self, data):
        offer = data.get("offer")
        sale_price = data.get("sale_price")

        if offer and sale_price:
           raise serializers.ValidationError({
            "offer": "Remove offer before setting sale price"
        })

        return data

    
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

    # 🔥 OFFER LOGIC FIX
        offer = validated_data.get("offer", None)

        if offer:
           instance.sale_price = None  # ✅ AUTO REMOVE SALE PRICE

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if collections is not None:
           instance.collections.set(collections)

        if images:
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
    user_email = serializers.CharField(source="user.email", read_only=True)
    items = serializers.SerializerMethodField()
    address_details = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user_email",

            "subtotal_amount",
            "discount_amount",
            "shipping_amount",
            "gst_amount",
            "total_amount",

            "payment_status",
            "status",
            "courier_name",
            "tracking_id",
            "created_at",

            "address_details",
            "items",
        ]

    def get_items(self, obj):
        items = []
        for item in obj.items.all():
            items.append({
                "id": item.id,
                "quantity": item.quantity,
                "price": item.price,
                "color": item.color,

                "size": item.variant.size if item.variant else None,

                "product": ProductSerializer(
    item.variant.product,
    context=self.context   # ⭐ THIS IS THE FIX
).data if item.variant else None,

            })
        return items

    def get_address_details(self, obj):
        address = obj.address
        if not address:
            return None

        return {
            "name": address.name,
            "phone": address.phone,
            "pincode": address.pincode,
            "city": address.city,
            "state": address.state,
            "full_address": address.full_address,
        }


class AdminOrderShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "status",
            "courier_name",
            "tracking_id",
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






class AdminCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"

    def validate_code(self, value):
        value = value.strip().upper()

        if len(value) < 4:
            raise serializers.ValidationError(
                "Coupon code must be at least 4 characters"
            )

        return value

    def validate_discount_value(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Discount value must be greater than 0"
            )
        return value

    def validate_min_purchase(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Minimum purchase cannot be negative"
            )
        return value

    def validate(self, data):
        discount_type = data.get(
            "discount_type",
            self.instance.discount_type if self.instance else None
        )
        discount_value = data.get(
            "discount_value",
            self.instance.discount_value if self.instance else None
        )
        expiry_date = data.get(
            "expiry_date",
            self.instance.expiry_date if self.instance else None
        )
        usage_limit = data.get(
            "usage_limit",
            self.instance.usage_limit if self.instance else None
        )
        used_count = self.instance.used_count if self.instance else 0

        # Expiry date must be future
        if expiry_date and expiry_date <= timezone.now():
            raise serializers.ValidationError({
                "expiry_date": "Expiry date must be in the future"
            })

        # Percent discount cannot exceed 100
        if discount_type == "PERCENT" and discount_value > 100:
            raise serializers.ValidationError({
                "discount_value": "Percentage discount cannot exceed 100"
            })

        # Usage limit logic
        if usage_limit is not None and usage_limit < used_count:
            raise serializers.ValidationError({
                "usage_limit": "Usage limit cannot be less than used count"
            })

        return data





class AdminOfferSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    products_count = serializers.IntegerField(
        source="products.count",
        read_only=True
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
            "products_count",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["slug", "created_at"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None

    # 🔥🔥🔥 ADD THIS METHOD HERE 🔥🔥🔥
    def validate(self, data):
        start_date = data.get("start_date") or (
            self.instance.start_date if self.instance else None
        )
        end_date = data.get("end_date") or (
            self.instance.end_date if self.instance else None
        )
        discount_type = data.get("discount_type") or (
            self.instance.discount_type if self.instance else None
        )
        discount_value = data.get("discount_value") or (
            self.instance.discount_value if self.instance else None
        )

        # ✅ Ensure datetime objects (multipart fix)
        if isinstance(start_date, str):
            start_date = parse_datetime(start_date)
        if isinstance(end_date, str):
            end_date = parse_datetime(end_date)

        # ✅ Date validation
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date"
            })

        # ✅ Discount validation
        if discount_value is not None and discount_value < 0:
            raise serializers.ValidationError({
                "discount_value": "Discount value cannot be negative"
            })

        if discount_type == "PERCENT" and discount_value > 90:
            raise serializers.ValidationError({
                "discount_value": "Percentage discount cannot exceed 90%"
            })

        return data
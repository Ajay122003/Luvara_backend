from rest_framework import serializers
from decimal import Decimal
from django.utils.timezone import now
from admin_panel.models import SiteSettings
from django.db import transaction
from .models import Order, OrderItem, ReturnRequest
from products.models import Product ,ProductVariant
from addresses.models import Address
from products.serializers import ProductSerializer
from .utils import generate_order_number
from coupons.models import Coupon
from django.utils import timezone
from cart.models import CartItem

GST_PERCENTAGE = Decimal("3.00")


class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(
        required=False, allow_null=True
    )
    delivery_address = serializers.DictField(
        required=False
    )
    billing_address = serializers.DictField(
        required=False, allow_null=True
    )
    coupon_code = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    payment_method = serializers.ChoiceField(
        choices=["COD", "ONLINE"]
    )

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        # ---------- ADDRESS ----------
        address = None

        if data.get("address_id"):
            try:
                address = Address.objects.get(
                    id=data["address_id"],
                    user=user,
                    is_temporary=False
                )
            except Address.DoesNotExist:
                raise serializers.ValidationError(
                    {"address_id": "Invalid address"}
                )

        elif data.get("delivery_address"):
            addr = data["delivery_address"]
            required = ["name", "phone", "pincode", "city", "full_address"]
            for f in required:
                if not addr.get(f):
                    raise serializers.ValidationError(
                        {f: "This field is required"}
                    )

            address = Address.objects.create(
                user=user,
                name=addr["name"],
                phone=addr["phone"],
                pincode=addr["pincode"],
                city=addr["city"],
                state=addr.get("state", ""),
                full_address=addr["full_address"],
                is_temporary=not addr.get("save_for_future", False),
            )
        else:
            raise serializers.ValidationError(
                "Delivery address required"
            )

        # ---------- CART ----------
        cart_items = CartItem.objects.select_for_update().filter(user=user)
        if not cart_items.exists():
            raise serializers.ValidationError(
                {"items": "Cart is empty"}
            )

        subtotal = Decimal("0.00")
        for item in cart_items:
            if item.variant.stock < item.quantity:
                raise serializers.ValidationError(
                    f"Not enough stock for {item.variant.product.name}"
                )

            price = (
                item.variant.product.sale_price
                or item.variant.product.price
            )
            subtotal += Decimal(price) * item.quantity

        # ---------- COUPON ----------
        coupon_obj = None
        discount = Decimal("0.00")
        coupon_code = (data.get("coupon_code") or "").strip()

        if coupon_code:
            try:
                coupon_obj = Coupon.objects.select_for_update().get(
                    code__iexact=coupon_code,
                    is_active=True
                )
            except Coupon.DoesNotExist:
                raise serializers.ValidationError(
                    {"coupon_code": "Invalid coupon"}
                )

            if timezone.now() > coupon_obj.expiry_date:
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon expired"}
                )

            if coupon_obj.used_count >= coupon_obj.usage_limit:
                raise serializers.ValidationError(
                    {"coupon_code": "Usage limit exceeded"}
                )

            if subtotal < coupon_obj.min_purchase:
                raise serializers.ValidationError(
                    {"coupon_code": "Minimum purchase not met"}
                )

            if coupon_obj.discount_type == "PERCENT":
                discount = (
                    Decimal(coupon_obj.discount_value) / 100
                ) * subtotal
            else:
                discount = Decimal(coupon_obj.discount_value)

            discount = min(discount, subtotal)

        # ---------- SHIPPING ----------
        settings = SiteSettings.objects.first()
        shipping_amount = (
            settings.shipping_charge
            if subtotal - discount < settings.free_shipping_min_amount
            else Decimal("0.00")
        )

        # ---------- GST ----------
        taxable = subtotal - discount + shipping_amount
        gst_amount = (taxable * GST_PERCENTAGE) / 100
        total = taxable + gst_amount

        data.update({
            "address_obj": address,
            "cart_items": cart_items,
            "subtotal": subtotal,
            "discount": discount,
            "shipping_amount": shipping_amount,
            "gst_amount": gst_amount,
            "total": total,
            "coupon_obj": coupon_obj,
        })

        return data

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user

        order = Order.objects.create(
            user=user,
            address=validated_data["address_obj"],
            order_number=generate_order_number(),
            subtotal_amount=validated_data["subtotal"],
            discount_amount=validated_data["discount"],
            shipping_amount=validated_data["shipping_amount"],
            gst_percentage=GST_PERCENTAGE,
            gst_amount=validated_data["gst_amount"],
            total_amount=validated_data["total"],
            coupon=validated_data["coupon_obj"],
            payment_status="PENDING",
        )

        for item in validated_data["cart_items"]:
            price = (
                item.variant.product.sale_price
                or item.variant.product.price
            )

            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                price=price,
                color=item.variant.color, 
            )

            item.variant.stock -= item.quantity
            item.variant.save()

        validated_data["cart_items"].delete()

        if validated_data["coupon_obj"]:
            coupon = validated_data["coupon_obj"]
            coupon.used_count += 1
            coupon.save(update_fields=["used_count"])

        return order


# ================= READ SERIALIZERS =================

class OrderItemDetailSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "size",
            "quantity",
            "price",
            "color",
        ]

    def get_product(self, obj):
        request = self.context.get("request")   # 🔥 IMPORTANT
        if obj.variant and obj.variant.product:
            return ProductSerializer(
                obj.variant.product,
                context={"request": request}    # 🔥 PASS REQUEST
            ).data
        return None

    def get_size(self, obj):
        return obj.variant.size if obj.variant else None




class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(many=True)
    address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "subtotal_amount",
            "discount_amount",
            "shipping_amount",
            "gst_percentage",
            "gst_amount",
            "total_amount",
            "payment_status",
            "status",
            "courier_name",
            "tracking_id",
            "created_at",
            "address",
            "items",
        ]

    def get_address(self, obj):
        if obj.address:
            return {
                "name": obj.address.name,
                "phone": obj.address.phone,
                "pincode": obj.address.pincode,
                "city": obj.address.city,
                "state": obj.address.state,
                "full_address": obj.address.full_address,
            }
        return None


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "total_amount",
            "payment_status",
            "status",
            "created_at",
        ]


class ReturnRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnRequest
        fields = ["id", "order", "reason", "status", "created_at"]
        read_only_fields = ["status", "created_at", "order"]

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

GST_PERCENTAGE = Decimal("3.00")


class OrderItemInputSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False)
    delivery_address = serializers.DictField(required=False)
    billing_address = serializers.DictField(required=False)

    items = OrderItemInputSerializer(many=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        # ---------------- ADDRESS ----------------
        address = None
        if data.get("address_id"):
            try:
                address = Address.objects.get(
                    id=data["address_id"], user=user, is_temporary=False
                )
            except Address.DoesNotExist:
                raise serializers.ValidationError("Invalid address")

        elif data.get("delivery_address"):
            addr = data["delivery_address"]
            required = ["name", "phone", "pincode", "city", "full_address"]
            for f in required:
                if not addr.get(f):
                    raise serializers.ValidationError(f"{f} is required")

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
            raise serializers.ValidationError("Delivery address required")

        # ---------------- VARIANTS ----------------
        variant_ids = [i["variant_id"] for i in data["items"]]

        variants = {
            v.id: v
            for v in ProductVariant.objects.select_for_update().filter(
                id__in=variant_ids, product__is_active=True
            )
        }

        if len(variants) != len(set(variant_ids)):
            raise serializers.ValidationError("Invalid product variant")

        subtotal = Decimal("0.00")
        for item in data["items"]:
            variant = variants[item["variant_id"]]
            if variant.stock < item["quantity"]:
                raise serializers.ValidationError(
                    f"Not enough stock for {variant.product.name}"
                )

            price = variant.product.sale_price or variant.product.price
            subtotal += Decimal(price) * item["quantity"]

        # ---------------- COUPON ----------------
        coupon_obj = None
        discount = Decimal("0.00")
        coupon_code = data.get("coupon_code", "").strip()

        if coupon_code:
            try:
                coupon_obj = Coupon.objects.select_for_update().get(
                    code__iexact=coupon_code
                )
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid coupon")

            if not coupon_obj.is_active:
                raise serializers.ValidationError("Coupon inactive")

            if timezone.now() > coupon_obj.expiry_date:
                raise serializers.ValidationError("Coupon expired")

            if coupon_obj.used_count >= coupon_obj.usage_limit:
                raise serializers.ValidationError("Coupon usage limit exceeded")

            if subtotal < Decimal(coupon_obj.min_purchase):
                raise serializers.ValidationError("Minimum purchase not met")

            if coupon_obj.discount_type == "PERCENT":
                discount = (Decimal(coupon_obj.discount_value) / 100) * subtotal
            else:
                discount = Decimal(coupon_obj.discount_value)

            discount = min(discount, subtotal)

        # ---------------- SHIPPING ----------------
        settings = SiteSettings.objects.first()
        shipping_amount = (
            settings.shipping_charge
            if subtotal - discount < settings.free_shipping_min_amount
            else Decimal("0.00")
        )

        # ---------------- GST ----------------
        taxable = subtotal - discount + shipping_amount
        gst_amount = (taxable * GST_PERCENTAGE) / 100
        grand_total = taxable + gst_amount

        data.update({
            "address_obj": address,
            "variants_cache": variants,
            "subtotal": subtotal,
            "discount": discount,
            "shipping_amount": shipping_amount,
            "gst_amount": gst_amount,
            "grand_total": grand_total,
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
            total_amount=validated_data["grand_total"],
            coupon=validated_data["coupon_obj"],
            payment_status="PENDING",
        )

        for item in validated_data["items"]:
            variant = validated_data["variants_cache"][item["variant_id"]]
            price = variant.product.sale_price or variant.product.price

            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=item["quantity"],
                price=price,
            )

            variant.stock -= item["quantity"]
            variant.save()

        #  INCREMENT COUPON USAGE
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
        if obj.variant and obj.variant.product:
            return obj.variant.product.name
        return None

    def get_size(self, obj):
        if obj.variant:
            return obj.variant.size
        return None


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

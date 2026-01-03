from rest_framework import serializers
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import Order, OrderItem, ReturnRequest
from products.models import ProductVariant
from addresses.models import Address
from products.serializers import ProductSerializer
from .utils import generate_order_number, send_admin_new_order_alert
from coupons.models import Coupon
from cart.models import CartItem
from admin_panel.models import SiteSettings

GST_PERCENTAGE = Decimal("3.00")


# ======================================================
# ORDER CREATE
# ======================================================
class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False, allow_null=True)
    delivery_address = serializers.DictField(required=False)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=["COD", "ONLINE"])

    # --------------------------------------------------
    # VALIDATE
    # --------------------------------------------------
    def validate(self, data):
        request = self.context["request"]
        user = request.user

        # ---------------- ADDRESS ----------------
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

            for field in required:
                if not addr.get(field):
                    raise serializers.ValidationError(
                        {field: "This field is required"}
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

        # ---------------- CART ----------------
        cart_items = (
            CartItem.objects
            .select_for_update()
            .select_related("variant", "variant__product", "variant__product__offer")
            .filter(user=user)
        )

        if not cart_items.exists():
            raise serializers.ValidationError(
                {"cart": "Cart is empty"}
            )

        subtotal = Decimal("0.00")

        for item in cart_items:
            if item.variant.stock < item.quantity:
                raise serializers.ValidationError(
                    f"Not enough stock for {item.variant.product.name}"
                )

            unit_price = item.variant.product.get_effective_price()
            subtotal += unit_price * item.quantity

        
        # ---------------- COUPON ----------------
        coupon_obj = None
        discount = Decimal("0.00")

        coupon_code = data.get("coupon_code", None)

# ✅ If coupon_code is None or empty → SKIP
        if coupon_code:
            coupon_code = coupon_code.strip()

            if coupon_code:  # 🔥 strip pannina apram check
                try:
                  coupon_obj = Coupon.objects.select_for_update().get(
                  code__iexact=coupon_code,
                  is_active=True
               )
                except Coupon.DoesNotExist:
                   raise serializers.ValidationError({
                   "coupon_code": "Invalid coupon"
                })

        # expiry check
                if coupon_obj.expiry_date < timezone.now():
                  raise serializers.ValidationError({
                   "coupon_code": "Coupon expired"
                })

        # usage limit
                if coupon_obj.used_count >= coupon_obj.usage_limit:
                  raise serializers.ValidationError({
                "coupon_code": "Coupon usage limit exceeded"
                })

        # min purchase
                if subtotal < coupon_obj.min_purchase:
                   raise serializers.ValidationError({
                   "coupon_code": "Minimum purchase not met"
                 })

        # discount calculation
                if coupon_obj.discount_type == "PERCENT":
                   discount = (Decimal(coupon_obj.discount_value) / 100) * subtotal
                else:
                   discount = Decimal(coupon_obj.discount_value)

                discount = min(discount, subtotal)


        # ---------------- SHIPPING ----------------
        settings = SiteSettings.objects.first()
        shipping_amount = Decimal("0.00")

        if settings and settings.shipping_charge > 0:
    # Case 1: free_shipping_min_amount = 0 → always charge shipping
           if settings.free_shipping_min_amount == 0:
              shipping_amount = settings.shipping_charge

    # Case 2: subtotal < free shipping limit → charge shipping
           elif subtotal - discount < settings.free_shipping_min_amount:
               shipping_amount = settings.shipping_charge


        # ---------------- GST ----------------
        taxable_amount = subtotal - discount + shipping_amount
        gst_amount = (taxable_amount * GST_PERCENTAGE) / 100
        total_amount = taxable_amount + gst_amount

        data.update({
            "address_obj": address,
            "cart_items": cart_items,
            "subtotal": subtotal,
            "discount": discount,
            "shipping_amount": shipping_amount,
            "gst_amount": gst_amount,
            "total": total_amount,
            "coupon_obj": coupon_obj,
        })

        return data

    # --------------------------------------------------
    # CREATE ORDER
    # --------------------------------------------------
    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user

        payment_method = validated_data["payment_method"]

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
    payment_method=payment_method,

    # 🔥 KEY PART
    payment_status="PENDING" if payment_method == "ONLINE" else "PAID",
)


        # ---------------- ORDER ITEMS ----------------
        for item in validated_data["cart_items"]:
            product = item.variant.product

            original_price = product.price
            unit_price = product.get_effective_price()
            total_price = unit_price * item.quantity

            OrderItem.objects.create(
                order=order,
                variant=item.variant,
                quantity=item.quantity,
                original_price=original_price,
                unit_price=unit_price,
                total_price=total_price,
                color=item.variant.color or "",
            )

            # Reduce stock
            item.variant.stock -= item.quantity
            item.variant.save(update_fields=["stock"])

        # Clear cart
        validated_data["cart_items"].delete()

        # Coupon usage update
        if validated_data["coupon_obj"]:
            coupon = validated_data["coupon_obj"]
            coupon.used_count += 1
            coupon.save(update_fields=["used_count"])

        
        return order


# ======================================================
# ORDER READ
# ======================================================
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
            "original_price",
            "unit_price",
            "total_price",
            "color",
        ]

    def get_product(self, obj):
        request = self.context.get("request")
        if obj.variant and obj.variant.product:
            return ProductSerializer(
                obj.variant.product,
                context={"request": request}
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
        if not obj.address:
            return None

        return {
            "name": obj.address.name,
            "phone": obj.address.phone,
            "pincode": obj.address.pincode,
            "city": obj.address.city,
            "state": obj.address.state,
            "full_address": obj.address.full_address,
        }


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
        fields = [
            "id",
            "order",
            "reason",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at", "order"]

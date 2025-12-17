from rest_framework import serializers
from decimal import Decimal
from django.utils.timezone import now
from admin_panel.models import SiteSettings

from .models import Order, OrderItem, ReturnRequest
from products.models import Product
from addresses.models import Address
from products.serializers import ProductSerializer
from .utils import generate_order_number
from coupons.models import Coupon

GST_PERCENTAGE = Decimal("3.00")



class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    size = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, allow_blank=True)


from rest_framework import serializers
from decimal import Decimal
from django.utils.timezone import now
from admin_panel.models import SiteSettings

from .models import Order, OrderItem, ReturnRequest
from products.models import Product
from addresses.models import Address
from products.serializers import ProductSerializer
from .utils import generate_order_number
from coupons.models import Coupon

GST_PERCENTAGE = Decimal("3.00")


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    size = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, allow_blank=True)


class OrderCreateSerializer(serializers.Serializer):
    # 🔥 DELIVERY ADDRESS OPTIONS
    address_id = serializers.IntegerField(required=False)
    delivery_address = serializers.DictField(required=False)

    # 🔥 BILLING ADDRESS (NEW)
    billing_address = serializers.DictField(required=False)

    items = OrderItemInputSerializer(many=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        # =====================================================
        # 📍 DELIVERY ADDRESS (saved OR new)
        # =====================================================
        address = None

        # Case 1️⃣ Saved address
        if data.get("address_id"):
            try:
                address = Address.objects.get(
                    id=data["address_id"],
                    user=user,
                    is_temporary=False
                )
            except Address.DoesNotExist:
                raise serializers.ValidationError("Invalid address")

        # Case 2️⃣ New delivery address
        elif data.get("delivery_address"):
            addr = data["delivery_address"]

            required = ["name", "phone", "pincode", "city", "full_address"]
            for f in required:
                if not addr.get(f):
                    raise serializers.ValidationError(
                        f"{f} is required in delivery address"
                    )

            address = Address.objects.create(
                user=user,
                name=addr["name"],
                phone=addr["phone"],
                pincode=addr["pincode"],
                city=addr["city"],
                state=addr.get("state", ""),
                full_address=addr["full_address"],
                is_temporary=not addr.get("save_for_future", False)
            )
        else:
            raise serializers.ValidationError("Delivery address is required")

        # =====================================================
        # 🧾 BILLING ADDRESS (optional)
        # =====================================================
        billing_addr = data.get("billing_address")

        if billing_addr:
            required = ["name", "phone", "pincode", "city", "full_address"]
            for f in required:
                if not billing_addr.get(f):
                    raise serializers.ValidationError(
                        f"{f} is required in billing address"
                    )

            data["billing_address_data"] = billing_addr
        else:
            data["billing_address_data"] = None  # same as delivery

        # =====================================================
        # 🛒 PRODUCTS + STOCK
        # =====================================================
        product_ids = [i["product_id"] for i in data["items"]]
        products = {
            p.id: p
            for p in Product.objects.filter(id__in=product_ids, is_active=True)
        }

        if len(products) != len(set(product_ids)):
            raise serializers.ValidationError("Invalid product")

        subtotal = Decimal("0.00")

        for item in data["items"]:
            product = products[item["product_id"]]

            if product.stock < item["quantity"]:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}"
                )

            price = product.sale_price or product.price
            subtotal += Decimal(str(price)) * item["quantity"]

        # =====================================================
        # 🎟️ COUPON
        # =====================================================
        coupon_obj = None
        discount = Decimal("0.00")
        final_amount = subtotal

        coupon_code = data.get("coupon_code", "").strip()
        if coupon_code:
            try:
                coupon_obj = Coupon.objects.get(code__iexact=coupon_code)
            except Coupon.DoesNotExist:
                raise serializers.ValidationError(
                    {"coupon_code": "Invalid coupon"}
                )

            if not coupon_obj.is_active or coupon_obj.expiry_date < now():
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon expired"}
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

            if discount > subtotal:
                discount = subtotal

            final_amount = subtotal - discount

        # =====================================================
        # 🚚 SHIPPING
        # =====================================================
        settings = SiteSettings.objects.first() or SiteSettings.objects.create()

        shipping_amount = (
            settings.shipping_charge
            if final_amount < settings.free_shipping_min_amount
            else Decimal("0.00")
        )

        # =====================================================
        # 🔥 GST
        # =====================================================
        taxable = final_amount + shipping_amount
        gst_amount = (taxable * GST_PERCENTAGE) / 100
        grand_total = taxable + gst_amount

        # =====================================================
        # STORE FOR CREATE()
        # =====================================================
        data["address_obj"] = address
        data["products_cache"] = products
        data["coupon_obj"] = coupon_obj

        data["subtotal"] = subtotal
        data["discount"] = discount
        data["shipping_amount"] = shipping_amount
        data["gst_percentage"] = GST_PERCENTAGE
        data["gst_amount"] = gst_amount
        data["grand_total"] = grand_total

        return data

    def create(self, validated_data):
        user = self.context["request"].user

        order = Order.objects.create(
            user=user,
            address=validated_data["address_obj"],
            order_number=generate_order_number(),

            subtotal_amount=validated_data["subtotal"],
            discount_amount=validated_data["discount"],
            shipping_amount=validated_data["shipping_amount"],
            gst_percentage=validated_data["gst_percentage"],
            gst_amount=validated_data["gst_amount"],
            total_amount=validated_data["grand_total"],

            coupon=validated_data["coupon_obj"],
            payment_status="PENDING",
            status="PENDING",
        )

        for item in validated_data["items"]:
            product = validated_data["products_cache"][item["product_id"]]
            price = product.sale_price or product.price

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                size=item.get("size", ""),
                color=item.get("color", ""),
                price=price,
            )

            product.stock -= item["quantity"]
            product.save()

        return order



# ================= READ SERIALIZERS =================

class OrderItemDetailSerializer(serializers.ModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price", "size", "color"]


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

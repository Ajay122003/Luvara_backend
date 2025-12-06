from rest_framework import serializers
from decimal import Decimal
from django.utils.timezone import now

from .models import Order, OrderItem, ReturnRequest
from products.models import Product
from addresses.models import Address
from products.serializers import ProductSerializer
from .utils import generate_order_number
from coupons.models import Coupon


class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    size = serializers.CharField(required=False, allow_blank=True)
    color = serializers.CharField(required=False, allow_blank=True)


class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    items = OrderItemInputSerializer(many=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        request = self.context["request"]
        user = request.user

        # ---------- Address validate ----------
        try:
            address = Address.objects.get(id=data["address_id"], user=user)
        except Address.DoesNotExist:
            raise serializers.ValidationError("Invalid address")

        # ---------- Product + stock validate ----------
        product_ids = [item["product_id"] for item in data["items"]]
        products = {
            p.id: p
            for p in Product.objects.filter(id__in=product_ids, is_active=True)
        }

        if len(products) != len(set(product_ids)):
            raise serializers.ValidationError("One or more products are invalid")

        # Calculate subtotal
        subtotal = Decimal("0.00")
        for item in data["items"]:
            product = products[item["product_id"]]
            if product.stock < item["quantity"]:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}. Only {product.stock} left."
                )
            price = product.sale_price or product.price
            subtotal += Decimal(str(price)) * item["quantity"]

        data["address_obj"] = address
        data["products_cache"] = products
        data["subtotal"] = subtotal

        # ---------- Coupon validate (if sent) ----------
        coupon_code = data.get("coupon_code", "").strip()
        coupon_obj = None
        discount = Decimal("0.00")
        final_amount = subtotal

        if coupon_code:
            try:
                coupon_obj = Coupon.objects.get(code__iexact=coupon_code)
            except Coupon.DoesNotExist:
                raise serializers.ValidationError(
                    {"coupon_code": "Invalid coupon code"}
                )

            if not coupon_obj.is_active:
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon is not active"}
                )

            if coupon_obj.expiry_date < now():
                raise serializers.ValidationError(
                    {"coupon_code": "Coupon expired"}
                )

            if subtotal < Decimal(str(coupon_obj.min_purchase)):
                raise serializers.ValidationError(
                    {
                        "coupon_code": f"Minimum purchase required: {coupon_obj.min_purchase}"
                    }
                )

            # Calculate discount
            if coupon_obj.discount_type == "PERCENT":
                discount = (
                    Decimal(str(coupon_obj.discount_value)) / Decimal("100")
                ) * subtotal
            else:  # FLAT
                discount = Decimal(str(coupon_obj.discount_value))

            # Ensure not more than subtotal
            if discount > subtotal:
                discount = subtotal

            final_amount = subtotal - discount

        data["coupon_obj"] = coupon_obj
        data["discount"] = discount
        data["final_amount"] = final_amount

        return data

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        address = validated_data["address_obj"]
        products = validated_data["products_cache"]

        subtotal = validated_data["subtotal"]
        discount = validated_data["discount"]
        final_amount = validated_data["final_amount"]
        coupon_obj = validated_data["coupon_obj"]

        # ---------- Create Order ----------
        order = Order.objects.create(
            user=user,
            address=address,
            total_amount=final_amount,           # store final amount
            order_number=generate_order_number(),
            payment_status="PENDING",
            status="PENDING",
            coupon=coupon_obj,
            discount_amount=discount,
        )

        # ---------- Create OrderItems + reduce stock ----------
        for item in validated_data["items"]:
            product = products[item["product_id"]]
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
            "total_amount",
            "discount_amount",
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

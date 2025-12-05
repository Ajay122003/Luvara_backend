from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from addresses.models import Address
from .utils import generate_order_number
from products.serializers import ProductSerializer

class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    size = serializers.CharField(required=False)
    color = serializers.CharField(required=False)


class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    items = OrderItemInputSerializer(many=True)

    def validate(self, data):
        # Check address belongs to user
        request = self.context["request"]
        user = request.user

        try:
            address = Address.objects.get(id=data["address_id"], user=user)
        except Address.DoesNotExist:
            raise serializers.ValidationError("Invalid address")

        # Validate product stock
        for item in data["items"]:
            try:
                product = Product.objects.get(id=item["product_id"], is_active=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError("Invalid product")

            if product.stock < item["quantity"]:
                raise serializers.ValidationError(f"Not enough stock for {product.name}")

        return data

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        address = Address.objects.get(id=validated_data["address_id"])

        # Calculate total
        total_amount = 0
        for item in validated_data["items"]:
            product = Product.objects.get(id=item["product_id"])
            price = product.sale_price if product.sale_price else product.price
            total_amount += price * item["quantity"]

        # Create Order
        order = Order.objects.create(
            user=user,
            address=address,
            total_amount=total_amount,
            order_number=generate_order_number(),
            payment_status="PENDING",
            status="PENDING",
        )

        # Create Order Items + Reduce Stock
        for item in validated_data["items"]:
            product = Product.objects.get(id=item["product_id"])
            price = product.sale_price if product.sale_price else product.price

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                size=item.get("size", ""),
                color=item.get("color", ""),
                price=price,
            )

            # Reduce stock
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
            "payment_status",
            "status",
            "created_at",
            "address",
            "items"
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
        fields = ["id", "order_number", "total_amount", "payment_status", "status", "created_at"]

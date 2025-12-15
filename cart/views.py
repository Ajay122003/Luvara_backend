from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import CartItem
from products.models import Product
from .serializers import CartItemSerializer

class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        size = request.data.get("size", "")
        color = request.data.get("color", "")

        if not product_id:
            return Response({"error": "product_id is required"}, status=400)

        if quantity < 1:
            return Response({"error": "Minimum quantity is 1"}, status=400)

        if quantity > 10:
            return Response({"error": "Maximum 10 items allowed"}, status=400)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        if quantity > product.stock:
            return Response({"error": "Not enough stock"}, status=400)

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            size=size,
            color=color,
            defaults={"quantity": quantity},
        )

        if not created:
            new_qty = cart_item.quantity + quantity

            if new_qty > 10:
                return Response({"error": "Max limit exceeded (10)"}, status=400)

            if new_qty > product.stock:
                return Response({"error": "Stock limit reached"}, status=400)

            cart_item.quantity = new_qty
            cart_item.save()

        serializer = CartItemSerializer(cart_item, context={"request": request})
        return Response(serializer.data, status=200)


class CartListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = (
            CartItem.objects.filter(user=request.user)
            .select_related("product")
            .order_by("-added_at")
        )

        serializer = CartItemSerializer(
            items, many=True, context={"request": request}
        )
        return Response(serializer.data)


class UpdateCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=404)

        quantity = int(request.data.get("quantity", item.quantity))

        if quantity < 1:
            return Response({"error": "Minimum quantity is 1"}, status=400)

        if quantity > 10:
            return Response({"error": "Max 10 items allowed"}, status=400)

        if quantity > item.product.stock:
            return Response({"error": "Stock not enough"}, status=400)

        item.quantity = quantity
        item.save()

        serializer = CartItemSerializer(item, context={"request": request})
        return Response(serializer.data)


class RemoveCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)

        item.delete()
        return Response({"message": "Item removed successfully"})

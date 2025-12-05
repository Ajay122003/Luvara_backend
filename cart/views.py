from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CartItem
from products.models import Product
from .serializers import CartItemSerializer

class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        size = request.data.get("size", "")
        color = request.data.get("color", "")

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        # Check stock
        if product.stock < quantity:
            return Response({"error": "Not enough stock"}, status=400)

        # If same product exists → increase quantity
        cart_item, created = CartItem.objects.get_or_create(
            user=user, product=product, size=size, color=color
        )

        cart_item.quantity += quantity
        cart_item.save()

        return Response({"message": "Added to cart successfully"})

class CartListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

class UpdateCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=404)

        quantity = int(request.data.get("quantity", item.quantity))

        if item.product.stock < quantity:
            return Response({"error": "Not enough stock"}, status=400)

        item.quantity = quantity
        item.save()

        return Response({"message": "Cart updated successfully"})


class RemoveCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, user=request.user)
        except CartItem.DoesNotExist:
            return Response({"error": "Cart item not found"}, status=404)

        item.delete()
        return Response({"message": "Item removed from cart"})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from rest_framework import status

from .models import CartItem
from products.models import ProductVariant
from .serializers import CartItemSerializer


class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        variant_id = request.data.get("variant_id")
        quantity = int(request.data.get("quantity", 1))

        if not variant_id:
            return Response(
                {"error": "variant_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity < 1:
            return Response(
                {"error": "Minimum quantity is 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity > 10:
            return Response(
                {"error": "Maximum 10 items allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            variant = ProductVariant.objects.select_for_update().get(
                id=variant_id, product__is_active=True
            )
        except ProductVariant.DoesNotExist:
            return Response(
                {"error": "Product variant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if quantity > variant.stock:
            return Response(
                {"error": "Not enough stock"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            variant=variant,
            defaults={"quantity": quantity},
        )

        if not created:
            new_qty = cart_item.quantity + quantity

            if new_qty > 10:
                return Response(
                    {"error": "Max limit exceeded (10)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if new_qty > variant.stock:
                return Response(
                    {"error": "Stock limit reached"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            cart_item.quantity = new_qty
            cart_item.save()

        serializer = CartItemSerializer(
            cart_item, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = (
            CartItem.objects.filter(user=request.user)
            .select_related("variant", "variant__product")
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
            item = CartItem.objects.select_related("variant").get(
                id=item_id, user=request.user
            )
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        quantity = int(request.data.get("quantity", item.quantity))

        if quantity < 1:
            return Response(
                {"error": "Minimum quantity is 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity > 10:
            return Response(
                {"error": "Max 10 items allowed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity > item.variant.stock:
            return Response(
                {"error": "Stock not enough"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = quantity
        item.save()

        serializer = CartItemSerializer(
            item, context={"request": request}
        )
        return Response(serializer.data)


class RemoveCartItemAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = CartItem.objects.get(id=item_id, user=request.user)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        item.delete()
        return Response(
            {"message": "Item removed successfully"},
            status=status.HTTP_200_OK,
        )


# 🔥 NEW – CLEAR CART (ORDER SUCCESS)
class ClearCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response(
            {"message": "Cart cleared successfully"},
            status=status.HTTP_200_OK,
        )

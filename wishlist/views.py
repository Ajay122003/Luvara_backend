from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import WishlistItem
from .serializers import WishlistItemSerializer
from products.models import Product


class WishlistListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = WishlistItem.objects.filter(user=request.user).select_related("product")
        serializer = WishlistItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)


class WishlistToggleAPIView(APIView):
    """
    If product not in wishlist → ADD
    If already in wishlist → REMOVE
    Frontend can use this for single  button.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")

        if not product_id:
            return Response({"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            return Response({"message": "Added to wishlist"}, status=status.HTTP_201_CREATED)
        else:
            item.delete()
            return Response({"message": "Removed from wishlist"}, status=status.HTTP_200_OK)


class WishlistRemoveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = WishlistItem.objects.get(id=item_id, user=request.user)
        except WishlistItem.DoesNotExist:
            return Response({"error": "Wishlist item not found"}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response({"message": "Wishlist item removed"}, status=status.HTTP_200_OK)

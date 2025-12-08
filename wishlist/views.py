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
        items = WishlistItem.objects.filter(
            user=request.user,
            product__is_active=True
        ).select_related("product")

        serializer = WishlistItemSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)
        

class WishlistToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")

        if not product_id:
            return Response({"error": "product_id is required"}, status=400)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            return Response({
                "message": "Added to wishlist",
                "is_added": True,
                "product_id": product_id
            }, status=201)

        item.delete()
        return Response({
            "message": "Removed from wishlist",
            "is_added": False,
            "product_id": product_id
        }, status=200)


class WishlistRemoveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        try:
            item = WishlistItem.objects.get(id=item_id, user=request.user)
        except WishlistItem.DoesNotExist:
            return Response({"error": "Wishlist item not found"}, status=404)

        product_id = item.product.id
        item.delete()

        return Response({
            "message": "Wishlist item removed",
            "product_id": product_id
        }, status=200)


class WishlistStatusAPIView(APIView):
    """
    Check if product is wishlisted
    GET /api/wishlist/status/?product_id=5
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.GET.get("product_id")

        if not product_id:
            return Response({"error": "product_id is required"}, status=400)

        exists = WishlistItem.objects.filter(
            user=request.user,
            product_id=product_id
        ).exists()

        return Response({"product_id": product_id, "is_added": exists})

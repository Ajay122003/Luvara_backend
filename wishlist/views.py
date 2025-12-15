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
        items = (
            WishlistItem.objects.filter(
                user=request.user,
                product__is_active=True
            )
            .select_related("product")
            .order_by("-created_at")
        )

        serializer = WishlistItemSerializer(
            items, many=True, context={"request": request}
        )
        return Response(serializer.data)


class WishlistToggleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(
                id=product_id,
                is_active=True
            )
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            return Response(
                {
                    "product_id": product_id,
                    "is_added": True,
                    "message": "Added to wishlist"
                },
                status=status.HTTP_201_CREATED
            )

        item.delete()
        return Response(
            {
                "product_id": product_id,
                "is_added": False,
                "message": "Removed from wishlist"
            },
            status=status.HTTP_200_OK
        )

class WishlistStatusAPIView(APIView):
    """
    GET /api/wishlist/status/?product_id=5
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.GET.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        exists = WishlistItem.objects.filter(
            user=request.user,
            product_id=product_id
        ).exists()

        return Response(
            {
                "product_id": product_id,
                "is_added": exists
            }
        )


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

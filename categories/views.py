from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Category
from .serializers import CategorySerializer

# PUBLIC CATEGORY LIST (User Side)
class CategoryListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.filter(is_active=True).order_by("sort_order")
        serializer = CategorySerializer(categories, many=True, context={"request": request})
        return Response(serializer.data, status=200)


# PUBLIC CATEGORY DETAIL (User Side) — SLUG BASED
class CategoryDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            category = Category.objects.get(slug=slug, is_active=True)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)

        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data)



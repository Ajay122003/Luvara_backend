from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from .models import Product
from .serializers import ProductSerializer
from .filters import product_filter


class PublicProductListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Product.objects.filter(is_active=True)\
            .prefetch_related("variants", "images")

        queryset = product_filter(queryset, request.query_params)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        result = paginator.paginate_queryset(queryset, request)

        serializer = ProductSerializer(
            result, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)



class PublicProductDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            product = Product.objects.prefetch_related(
                "variants", "images"
            ).get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data)



class RelatedProductsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, is_active=True)
        except Product.DoesNotExist:
            return Response([])

        related = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)\
         .prefetch_related("variants", "images")[:4]

        serializer = ProductSerializer(
            related, many=True, context={"request": request}
        )
        return Response(serializer.data)



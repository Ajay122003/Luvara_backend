from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from .models import Product, ProductImage
from .serializers import ProductSerializer, ProductCreateSerializer
from .filters import product_filter
from admin_panel.permissions import IsAdminUserCustom
from json import loads


class ProductListCreateAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUserCustom()]
        return [AllowAny()]

    def get(self, request):
        queryset = Product.objects.filter(is_active=True)
        queryset = product_filter(queryset, request.query_params)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = ProductSerializer(result_page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product, context={"request": request}).data, status=201)
        return Response(serializer.errors, status=400)


class ProductDetailAPIView(APIView):

    permission_classes = [IsAdminUserCustom]

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        data = request.data.copy()

        if "sizes" in data:
            data["sizes"] = loads(data["sizes"])

        if "colors" in data:
            data["colors"] = loads(data["colors"])

        serializer = ProductSerializer(product, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()

            # NEW IMAGES
            if "images" in request.FILES:
                for img in request.FILES.getlist("images"):
                    ProductImage.objects.create(product=product, image=img)

            return Response(ProductSerializer(product, context={"request": request}).data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        product.delete()
        return Response({"message": "Product deleted"}, status=200)


class DeleteProductImageAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def delete(self, request, image_id):
        try:
            img = ProductImage.objects.get(id=image_id)
        except ProductImage.DoesNotExist:
            return Response({"error": "Image not found"}, status=404)

        img.delete()
        return Response({"message": "Image deleted"}, status=200)

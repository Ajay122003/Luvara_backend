from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import *
from rest_framework.permissions import AllowAny

class ProductListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        products = Product.objects.filter(is_active=True).order_by("-id")
        serializer = ProductSerializer(products, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product, context={"request": request}).data, status=201)

        return Response(serializer.errors, status=400)


class ProductDetailAPIView(APIView):

    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        # Normal fields update
        data = request.data.copy()

        # Convert JSON text → Python list
        if "sizes" in data:
            from json import loads
            data["sizes"] = loads(data["sizes"])

        if "colors" in data:
            from json import loads
            data["colors"] = loads(data["colors"])

        serializer = ProductSerializer(product, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # NEW IMAGES UPLOAD
            if "images" in request.FILES:
                images = request.FILES.getlist("images")
                for img in images:
                    ProductImage.objects.create(product=product, image=img)

            return Response(ProductSerializer(product, context={"request": request}).data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        product.delete()
        return Response({"message": "Product deleted"}, status=200)


class DeleteProductImageAPIView(APIView):
    def delete(self, request, image_id):
        try:
            img = ProductImage.objects.get(id=image_id)
        except ProductImage.DoesNotExist:
            return Response({"error": "Image not found"}, status=404)

        img.delete()
        return Response({"message": "Image deleted"}, status=200)

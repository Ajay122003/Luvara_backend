from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AdminLoginSerializer
from categories.models import Category
from categories.serializers import CategorySerializer
from .permissions import IsAdminUserCustom
from products.models import Product
from products.serializers import ProductSerializer
from .serializers import AdminProductCreateSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from orders.models import Order
from .serializers import AdminOrderListSerializer, AdminOrderDetailSerializer



def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


class AdminLoginAPIView(APIView):
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            admin = serializer.validated_data
            tokens = generate_tokens(admin)
            return Response({
                "message": "Admin login successful",
                "tokens": tokens
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ----- TEST VIEW (Admin Protected) -----
class AdminTestAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        return Response({"message": "Admin access confirmed!"})


#CATEGORY
class AdminCategoryListCreateAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]  # for image uploads

    def get(self, request):
        categories = Category.objects.all().order_by("sort_order")
        serializer = CategorySerializer(categories, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AdminCategoryDetailAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=404)

        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=404)

        serializer = CategorySerializer(category, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response({"error": "Category not found"}, status=404)

        category.delete()
        return Response({"message": "Category deleted successfully"}, status=200)




# ADMIN PRODUCT LIST + CREATE
class AdminProductListCreateAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        products = Product.objects.all().order_by("-id")
        serializer = ProductSerializer(products, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = AdminProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product, context={"request": request}).data, status=201)

        return Response(serializer.errors, status=400)


# ADMIN PRODUCT DETAIL (GET / PUT / DELETE)
class AdminProductDetailAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

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

        serializer = AdminProductCreateSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            updated = Product.objects.get(pk=pk)
            return Response(ProductSerializer(updated, context={"request": request}).data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        product.delete()
        return Response({"message": "Product deleted successfully"}, status=200)



#ORDER MANAGE
class AdminOrderListAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        status_filter = request.GET.get("status")

        if status_filter:
            orders = Order.objects.filter(status=status_filter).order_by("-created_at")
        else:
            orders = Order.objects.all().order_by("-created_at")

        serializer = AdminOrderListSerializer(orders, many=True)
        return Response(serializer.data)


class AdminOrderDetailAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        serializer = AdminOrderDetailSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # Update only order status & payment status
        new_status = request.data.get("status")
        new_payment_status = request.data.get("payment_status")

        if new_status:
            order.status = new_status

        if new_payment_status:
            order.payment_status = new_payment_status

        order.save()

        return Response({"message": "Order updated successfully"})

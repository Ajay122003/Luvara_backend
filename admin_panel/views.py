# Core Django / DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from django.utils.timezone import now, timedelta

# Auth
from rest_framework_simplejwt.tokens import RefreshToken

# Permissions
from .permissions import IsAdminUserCustom

# Users
from users.models import User

# Categories
from categories.models import Category
from categories.serializers import CategorySerializer

# Products
from products.models import Product, ProductImage
from products.serializers import ProductSerializer
from .serializers import AdminProductCreateSerializer

# Orders
from orders.models import Order, OrderItem

# Admin Panel Serializers
from .serializers import AdminLoginSerializer

# NOTE:
# Avoid duplicate imports, unused imports, repeated modules.






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


# setting enable

class AdminSiteSettingsAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        settings, created = SiteSettings.objects.get_or_create(id=1)
        serializer = SiteSettingsSerializer(settings)
        return Response(serializer.data)

    def put(self, request):
        settings, created = SiteSettings.objects.get_or_create(id=1)
        serializer = SiteSettingsSerializer(settings, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Settings updated", "data": serializer.data})

        return Response(serializer.errors, status=400)


class AdminDashboardStatsAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):

        # 1. Total Users
        total_users = User.objects.count()

        # 2. Total Orders
        total_orders = Order.objects.count()

        # 3. Total Revenue (PAID + COD)
        total_revenue = (
            Order.objects.filter(payment_status__in=["PAID", "COD"])
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        # 4. Today's Orders
        today = now().date()
        todays_orders = Order.objects.filter(created_at__date=today).count()

        # 5. Today's Revenue
        todays_revenue = (
            Order.objects.filter(
                created_at__date=today,
                payment_status__in=["PAID", "COD"]
            ).aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        # 6. Pending Orders
        pending_orders = Order.objects.filter(status="PENDING").count()

        # 7. Delivered Orders
        delivered_orders = Order.objects.filter(status="DELIVERED").count()

        # 8. Best Selling Products (Top 5)
        best_sellers = (
            OrderItem.objects.values("product__name")
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        # 9. LOW STOCK ALERTS (NEW)
        LOW_STOCK_THRESHOLD = 5

        low_stock_count = Product.objects.filter(
            is_active=True,
            stock__lte=LOW_STOCK_THRESHOLD
        ).count()

        return Response({
            "total_users": total_users,
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "todays_orders": todays_orders,
            "todays_revenue": float(todays_revenue),
            "pending_orders": pending_orders,
            "delivered_orders": delivered_orders,
            "best_selling_products": list(best_sellers),

            # NEW FIELDS
            "low_stock_count": low_stock_count,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        })


class AdminLowStockProductsAPIView(APIView):
    """
    Returns list of products where stock is below a threshold.
    Default threshold = 5
    Admin-only access.
    """
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        # ?threshold=10  (optional)
        try:
            threshold = int(request.GET.get("threshold", 5))
        except ValueError:
            threshold = 5

        low_stock_products = Product.objects.filter(
            is_active=True,
            stock__lte=threshold
        ).order_by("stock")

        serializer = ProductSerializer(
            low_stock_products,
            many=True,
            context={"request": request}
        )

        return Response({
            "threshold": threshold,
            "count": len(serializer.data),
            "results": serializer.data
        })

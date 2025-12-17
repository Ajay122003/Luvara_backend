import logging
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from django.core.cache import cache
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Sum, Q

from .permissions import IsAdminUserCustom
from .models import SiteSettings, AdminOTP
from .serializers import *
from .utils_email import send_admin_otp_email, generate_otp
from subscriptions.models import Subscriber
from users.models import User
from categories.models import Category
from categories.serializers import *
from product_collections.models import Collection
from product_collections.serializers import *
from products.models import Product, ProductImage
from products.serializers import *
from orders.models import Order, OrderItem
from coupons.models import Coupon
from coupons.serializers import *

logger = logging.getLogger(__name__)


def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# -----------------------------
# ADMIN AUTH + PROFILE
# -----------------------------
class AdminLoginAPIView(APIView):
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            admin = serializer.validated_data

            otp = generate_otp()
            AdminOTP.objects.create(admin=admin, otp=otp)
            send_admin_otp_email(admin, otp)

            return Response(
                {"message": "OTP sent to admin email", "admin_email": admin.email}
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminVerifyOTPAPIView(APIView):
    def post(self, request):
        serializer = AdminOTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]

            try:
                admin_user = User.objects.get(email=email, is_staff=True)
            except User.DoesNotExist:
                return Response({"error": "Admin not found"}, status=404)

            try:
                latest_otp = AdminOTP.objects.filter(admin=admin_user).latest(
                    "created_at"
                )
            except AdminOTP.DoesNotExist:
                return Response({"error": "OTP not generated"}, status=400)

            if latest_otp.is_expired():
                return Response({"error": "OTP expired"}, status=400)

            if latest_otp.otp != otp:
                return Response({"error": "Invalid OTP"}, status=400)

            tokens = generate_tokens(admin_user)

            return Response(
                {
                    "message": "OTP verified successfully",
                    "tokens": tokens,
                }
            )

        return Response(serializer.errors, status=400)


class AdminUpdateEmailAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def put(self, request):
        serializer = AdminEmailChangeSerializer(data=request.data)
        if serializer.is_valid():
            new_email = serializer.validated_data["new_email"]

            admin = request.user
            admin.email = new_email
            admin.username = new_email  # if username = email
            admin.save()

            return Response(
                {"message": "Email updated successfully", "new_email": new_email}
            )

        return Response(serializer.errors, status=400)


class AdminChangePasswordAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def put(self, request):
        serializer = AdminPasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            admin = request.user
            admin.set_password(serializer.validated_data["new_password"])
            admin.save()
            return Response({"message": "Password updated successfully"})

        return Response(serializer.errors, status=400)

class AdminUserListView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        users = User.objects.all().values("id", "email", "username", "date_joined")
        return Response(users)


class AdminSubscriptionListView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        subs = Subscriber.objects.all().values("id", "email", "created_at")
        return Response(subs)


class AdminTestAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        return Response({"message": "Admin access confirmed!"})


# -----------------------------
# CATEGORY MANAGEMENT
# -----------------------------
class AdminCategoryListCreateAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        categories = Category.objects.all().order_by("sort_order", "name")
        serializer = CategorySerializer(
            categories, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = CategorySerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(
            category,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        if not category:
            return Response(
                {"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND
            )

        category.delete()
        return Response(
            {"message": "Category deleted successfully"},
            status=status.HTTP_200_OK,
        )


# -----------------------------
# collection MANAGEMENT
# -----------------------------

class AdminCollectionListCreateAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        collections = Collection.objects.all().order_by("sort_order", "name")
        serializer = CollectionListSerializer(
            collections, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = CollectionCreateUpdateSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            return Response(
                CollectionListSerializer(instance, context={"request": request}).data,
                status=201
            )
        return Response(serializer.errors, status=400)


class AdminCollectionDetailAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Collection.objects.get(pk=pk)
        except Collection.DoesNotExist:
            return None

    def get(self, request, pk):
        collection = self.get_object(pk)
        if not collection:
            return Response({"error": "Collection not found"}, status=404)

        serializer = CollectionListSerializer(collection, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        collection = self.get_object(pk)
        if not collection:
            return Response({"error": "Collection not found"}, status=404)

        serializer = CollectionCreateUpdateSerializer(
            collection,
            data=request.data,
            partial=True,
            context={"request": request}
        )
        if serializer.is_valid():
            instance = serializer.save()
            return Response(
                CollectionListSerializer(instance, context={"request": request}).data
            )
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        collection = self.get_object(pk)
        if not collection:
            return Response({"error": "Collection not found"}, status=404)

        collection.delete()
        return Response({"message": "Collection deleted successfully"}, status=200)
# -----------------------------
# PRODUCT MANAGEMENT
# -----------------------------
class AdminProductListCreateAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        products = Product.objects.all().order_by("-id")
        serializer = ProductSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductCreateSerializer(
            data=request.data,
            context={"request": request}   # ⭐ VERY IMPORTANT
        )

        if serializer.is_valid():
            product = serializer.save()
            return Response(
                ProductSerializer(product, context={"request": request}).data,
                status=201
            )

        return Response(serializer.errors, status=400)


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
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductSerializer(product, context={"request": request})
        return Response(serializer.data)

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminProductCreateSerializer(
            product, data=request.data, partial=True
        )
        if serializer.is_valid():
            updated_product = serializer.save()
            return Response(
                ProductSerializer(
                    updated_product, context={"request": request}
                ).data
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        product.delete()
        return Response(
            {"message": "Product deleted successfully"},
            status=status.HTTP_200_OK,
        )


class AdminDeleteProductImageAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def delete(self, request, image_id):
        try:
            img = ProductImage.objects.get(id=image_id)
        except ProductImage.DoesNotExist:
            return Response({"error": "Image not found"}, status=404)

        img.delete()
        return Response({"message": "Image deleted"}, status=200)


# -----------------------------
# ORDER MANAGEMENT
# -----------------------------
class AdminOrderListAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        status_filter = request.GET.get("status")

        if status_filter:
            orders = Order.objects.filter(status=status_filter).order_by(
                "-created_at"
            )
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
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = AdminOrderDetailSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")
        new_payment_status = request.data.get("payment_status")

        if new_status:
            order.status = new_status

        if new_payment_status:
            order.payment_status = new_payment_status

        order.save()

        return Response({"message": "Order updated successfully"})


# -----------------------------
# SITE SETTINGS (COD / CANCEL / RETURN)
# -----------------------------
class AdminSiteSettingsAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        settings_obj, created = SiteSettings.objects.get_or_create(id=1)
        serializer = SiteSettingsSerializer(settings_obj)
        return Response(serializer.data)

    def put(self, request):
        settings_obj, created = SiteSettings.objects.get_or_create(id=1)
        serializer = SiteSettingsSerializer(
            settings_obj, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Settings updated", "data": serializer.data}
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PublicSiteSettingsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        settings = SiteSettings.objects.first()

        if not settings:
            return Response({
                "enable_cod": False,
                "shipping_charge": 0,
                "free_shipping_min_amount": 0,
            })

        return Response({
            "enable_cod": settings.enable_cod,
            "shipping_charge": settings.shipping_charge,
            "free_shipping_min_amount": settings.free_shipping_min_amount,
        })



# -----------------------------
# DASHBOARD STATS + CACHE
# -----------------------------

class AdminDashboardStatsAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        # Try cache first
        cached_data = cache.get("admin_dashboard_stats")
        if cached_data:
            return Response(cached_data)

        # Summary stats
        total_users = User.objects.filter(is_staff=False).count()
        total_orders = Order.objects.count()

        total_subscribers = Subscriber.objects.count()

        total_revenue = (
            Order.objects.filter(
                Q(payment_status="PAID") |
                Q(payment_status="COD", status="DELIVERED")
            )
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        today = now().date()

        todays_orders = Order.objects.filter(created_at__date=today).count()

        todays_revenue = (
            Order.objects.filter(
                created_at__date=today
            )
            .filter(
                Q(payment_status="PAID") |
                Q(payment_status="COD", status="DELIVERED")
            )
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        pending_orders = Order.objects.filter(status="PENDING").count()
        delivered_orders = Order.objects.filter(status="DELIVERED").count()

        # BEST SELLERS — product info + single image
        best_sellers = (
            OrderItem.objects.values(
                "product_id",
                "product__name",
                "product__price",
                "product__sale_price",
            )
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        # Attach image manually for each product
        for item in best_sellers:
            from products.models import ProductImage
            img = ProductImage.objects.filter(product_id=item["product_id"]).first()
            item["image"] = img.image.url if img else None

        LOW_STOCK_THRESHOLD = 5

        low_stock_count = Product.objects.filter(
            is_active=True, stock__lte=LOW_STOCK_THRESHOLD
        ).count()

        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        total_categories = Category.objects.count()

        data = {
            "total_users": total_users,
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "todays_orders": todays_orders,
            "todays_revenue": float(todays_revenue),
            "pending_orders": pending_orders,
            "delivered_orders": delivered_orders,
            "best_selling_products": list(best_sellers),
            "low_stock_count": low_stock_count,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "total_products": total_products,
            "active_products": active_products,
            "total_categories": total_categories,
            "total_subscribers": total_subscribers,
        }

        cache.set("admin_dashboard_stats", data, timeout=60)
        return Response(data)



class AdminLowStockProductsAPIView(APIView):
    """
    Returns list of products where stock is below a threshold.
    Default threshold = 5
    Admin-only access.
    """

    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        try:
            threshold = int(request.GET.get("threshold", 5))
        except ValueError:
            threshold = 5

        low_stock_products = Product.objects.filter(
            is_active=True, stock__lte=threshold
        ).order_by("stock")

        serializer = ProductSerializer(
            low_stock_products,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "threshold": threshold,
                "count": len(serializer.data),
                "results": serializer.data,
            }
        )


# -----------------------------
# COUPON MANAGEMENT
# -----------------------------
class AdminCouponListCreateAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        coupons = Coupon.objects.all().order_by("-id")
        serializer = AdminCouponSerializer(coupons, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AdminCouponSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Coupon created", "data": serializer.data}, status=201
            )
        return Response(serializer.errors, status=400)


class AdminCouponDetailAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get_object(self, pk):
        try:
            return Coupon.objects.get(id=pk)
        except Coupon.DoesNotExist:
            return None

    def get(self, request, pk):
        coupon = self.get_object(pk)
        if not coupon:
            return Response({"error": "Coupon not found"}, status=404)

        serializer = AdminCouponSerializer(coupon)
        return Response(serializer.data)

    def put(self, request, pk):
        coupon = self.get_object(pk)
        if not coupon:
            return Response({"error": "Coupon not found"}, status=404)

        serializer = AdminCouponSerializer(coupon, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Coupon updated", "data": serializer.data}
            )

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        coupon = self.get_object(pk)
        if not coupon:
            return Response({"error": "Coupon not found"}, status=404)

        coupon.delete()
        return Response({"message": "Coupon deleted"}, status=200)
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
import json

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
        users = User.objects.filter(is_staff=False).values("id", "email", "username", "date_joined")
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
        data = request.data.copy()

        # 🔥 CREATE PRODUCT FIRST
        serializer = AdminProductCreateSerializer(data=data)
        if not serializer.is_valid():
            print("🔥 PRODUCT ERRORS 👉", serializer.errors)
            return Response(serializer.errors, status=400)

        product = serializer.save()

        # 🔥 CREATE VARIANTS MANUALLY
        i = 0
        while f"variants[{i}][size]" in request.data:
            ProductVariant.objects.create(
                product=product,
                size=request.data.get(f"variants[{i}][size]"),
                color=request.data.get(f"variants[{i}][color]"),
                stock=int(request.data.get(f"variants[{i}][stock]", 0)),
            )
            i += 1
        print("🔥 SERIALIZER ERRORS 👉", serializer.errors)
       
        return Response(
            ProductSerializer(product, context={"request": request}).data,
            status=201
        )

        


class AdminProductDetailAPIView(APIView):
    permission_classes = [IsAdminUserCustom]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    # -------- GET SINGLE PRODUCT --------
    def get(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        return Response(
            ProductSerializer(product, context={"request": request}).data
        )

    # -------- UPDATE PRODUCT --------
    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        data = request.data.copy()

        serializer = AdminProductCreateSerializer(
            product,
            data=data,
            partial=True
        )

        if not serializer.is_valid():
            print("🔥 PRODUCT UPDATE ERRORS 👉", serializer.errors)
            return Response(serializer.errors, status=400)

        updated_product = serializer.save()

        # 🔥 UPDATE VARIANTS (REPLACE ALL)
        ProductVariant.objects.filter(product=updated_product).delete()

        if "variants" in request.data:
            try:
                variants = json.loads(request.data.get("variants"))
            except Exception:
                return Response(
                    {"variants": ["Invalid format"]},
                    status=400
                )

            for v in variants:
                ProductVariant.objects.create(
                    product=updated_product,
                    size=v.get("size"),
                    color=v.get("color"),
                    stock=v.get("stock", 0),
                )
        print(" SERIALIZER ERRORS ", serializer.errors)
        return Response(
            ProductSerializer(updated_product, context={"request": request}).data,
            status=200
        )

    # -------- DELETE PRODUCT --------
    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({"error": "Product not found"}, status=404)

        product.delete()
        return Response({"message": "Product deleted"}, status=200)

class AdminDeleteProductImageAPIView(APIView):
    permission_classes = [IsAdminUserCustom]

    def delete(self, request, image_id):
        try:
            img = ProductImage.objects.get(id=image_id)
        except ProductImage.DoesNotExist:
            return Response(
                {"error": "Image not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        img.delete()
        return Response(
            {"message": "Image deleted successfully"},
            status=status.HTTP_200_OK,
        )

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
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminOrderDetailSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        new_status = request.data.get("status")
        new_payment_status = request.data.get("payment_status")

        if new_status:
            order.status = new_status

        if new_payment_status:
            order.payment_status = new_payment_status

        order.save()

        return Response(
            {"message": "Order updated successfully"},
            status=status.HTTP_200_OK,
        )


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
        # ---------------- CACHE ----------------
        cached_data = cache.get("admin_dashboard_stats")
        if cached_data:
            return Response(cached_data)

        # ---------------- BASIC COUNTS ----------------
        total_users = User.objects.filter(is_staff=False).count()
        total_orders = Order.objects.count()
        total_subscribers = Subscriber.objects.count()

        # ---------------- REVENUE ----------------
        total_revenue = (
            Order.objects.filter(
                Q(payment_status="PAID") |
                Q(payment_status="COD", status="DELIVERED")
            )
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        today = now().date()

        todays_orders = Order.objects.filter(
            created_at__date=today
        ).count()

        todays_revenue = (
            Order.objects.filter(created_at__date=today)
            .filter(
                Q(payment_status="PAID") |
                Q(payment_status="COD", status="DELIVERED")
            )
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        pending_orders = Order.objects.filter(status="PENDING").count()
        delivered_orders = Order.objects.filter(status="DELIVERED").count()

        # ---------------- BEST SELLERS (VARIANT → PRODUCT) ----------------
        best_sellers = (
            OrderItem.objects
            .values(
                "variant__product_id",
                "variant__product__name",
                "variant__product__price",
                "variant__product__sale_price",
            )
            .annotate(total_sold=Sum("quantity"))
            .order_by("-total_sold")[:5]
        )

        # Attach product image
        for item in best_sellers:
            img = ProductImage.objects.filter(
                product_id=item["variant__product_id"]
            ).first()
            item["image"] = img.image.url if img else None

        # ---------------- LOW STOCK (BASED ON VARIANTS) ----------------
        LOW_STOCK_THRESHOLD = 5

        low_stock_count = (
            Product.objects
            .filter(
                variants__stock__lte=LOW_STOCK_THRESHOLD,
                is_active=True
            )
            .distinct()
            .count()
        )

        # ---------------- PRODUCT / CATEGORY COUNTS ----------------
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        total_categories = Category.objects.count()

        # ---------------- FINAL RESPONSE ----------------
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
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        try:
            threshold = int(request.GET.get("threshold", 5))
        except ValueError:
            threshold = 5

        # 🔥 Find products where ANY variant stock <= threshold
        low_stock_products = (
            Product.objects
            .filter(
                variants__stock__lte=threshold,
                is_active=True
            )
            .distinct()
            .prefetch_related("variants", "images")
        )

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
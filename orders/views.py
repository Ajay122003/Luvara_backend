from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import FileResponse

from .serializers import (
    OrderCreateSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    ReturnRequestSerializer,
)
from .models import Order, ReturnRequest
from admin_panel.models import SiteSettings
from .utils_invoice import generate_invoice_pdf
from .utils import send_order_invoice_email


class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        settings_obj = SiteSettings.objects.first()

        payment_method = request.data.get("payment_method", "ONLINE")

        # ---------- COD availability ----------
        if payment_method == "COD":
            if not settings_obj or not settings_obj.enable_cod:
                return Response(
                    {"error": "COD is disabled"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = OrderCreateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            order = serializer.save()

            # ---------- Payment status ----------
            if payment_method == "COD":
                order.payment_status = "COD"
            else:
                order.payment_status = "PENDING"  # Razorpay

            order.save()

            # ---------- Invoice + Email ----------
            pdf_path = generate_invoice_pdf(order)
            send_order_invoice_email(order, pdf_path)

            return Response(
                {
                    "message": "Order created successfully",
                    "order_id": order.id,
                    "order_number": order.order_number,

                    # ---- PRICE BREAKUP ----
                    "subtotal": float(order.subtotal_amount),
                    "discount": float(order.discount_amount),
                    "shipping": float(order.shipping_amount),
                    "gst_percentage": float(order.gst_percentage),
                    "gst_amount": float(order.gst_amount),
                    "total_amount": float(order.total_amount),

                    "payment_status": order.payment_status,
                    "coupon_code": (request.data.get("coupon_code") or "").strip()

                    or None,
                },
                status=status.HTTP_201_CREATED,
            )
        print("ORDER CREATE ERROR ", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserOrderListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)


class UserOrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        serializer = OrderDetailSerializer(order)

        settings_obj = SiteSettings.objects.first()
        if not settings_obj:
            settings_obj = SiteSettings.objects.create()

        response = serializer.data

        response["can_cancel"] = (
            settings_obj.allow_order_cancel
            and order.status in ["PENDING", "PROCESSING"]
        )

        response["can_return"] = (
            settings_obj.allow_order_return
            and order.status == "DELIVERED"
        )

        response["cod_enabled"] = settings_obj.enable_cod

        return Response(response)


class CancelOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        settings_obj = SiteSettings.objects.first()
        if not settings_obj or not settings_obj.allow_order_cancel:
            return Response(
                {"error": "Order cancellation is disabled"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status not in ["PENDING", "PROCESSING"]:
            return Response(
                {"error": "This order cannot be cancelled now"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = "CANCELLED"
        order.save()

        # ---------- RESTORE VARIANT STOCK ----------
        for item in order.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()

        return Response(
            {"message": "Order cancelled successfully"},
            status=status.HTTP_200_OK,
        )


class RequestReturnAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        settings_obj = SiteSettings.objects.first()
        if not settings_obj or not settings_obj.allow_order_return:
            return Response(
                {"error": "Returns are disabled"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if order.status != "DELIVERED":
            return Response(
                {"error": "Only delivered orders can be returned"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if ReturnRequest.objects.filter(
            order=order, user=request.user
        ).exists():
            return Response(
                {"error": "Return already requested"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "")
        if not reason:
            return Response(
                {"error": "Reason is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ReturnRequest.objects.create(
            order=order, user=request.user, reason=reason
        )

        return Response(
            {"message": "Return request submitted"},
            status=status.HTTP_201_CREATED,
        )


class OrderInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        file_path = generate_invoice_pdf(order)

        return FileResponse(
            open(file_path, "rb"),
            content_type="application/pdf",
        )

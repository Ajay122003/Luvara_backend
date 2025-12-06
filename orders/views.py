from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import OrderCreateSerializer
from .models import Order
from products.serializers import ProductSerializer
from .models import Order
from .serializers import *
from admin_panel.models import SiteSettings
from django.http import FileResponse
from .utils_invoice import generate_invoice_pdf


class OrderCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        settings = SiteSettings.objects.first()

        payment_method = request.data.get("payment_method", "ONLINE")  # default = ONLINE

        # -------- COD availability check --------
        if payment_method == "COD":
            if not settings or not settings.enable_cod:
                return Response({"error": "COD is disabled"}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderCreateSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            order = serializer.save()

            # Payment status
            if payment_method == "COD":
                order.payment_status = "COD"
            else:
                order.payment_status = "PENDING"  # Razorpay pending

            order.save()

            return Response(
                {
                    "message": "Order created successfully",
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "subtotal": float(serializer.validated_data["subtotal"]),
                    "discount": float(serializer.validated_data["discount"]),
                    "total_amount": float(order.total_amount),
                    "payment_status": order.payment_status,
                    "coupon_code": request.data.get("coupon_code", "").strip() or None,
                },
                status=status.HTTP_201_CREATED,
            )

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

        # Fetch admin settings
        settings = SiteSettings.objects.first()
        if not settings:
            # If no settings row exists, create default one
            settings = SiteSettings.objects.create()

        response = serializer.data

        # Add user-side permissions
        response["can_cancel"] = (
            settings.allow_order_cancel
            and order.status in ["PENDING", "PROCESSING"]
        )

        response["can_return"] = (
            settings.allow_order_return
            and order.status == "DELIVERED"
        )

        response["cod_enabled"] = settings.enable_cod

        return Response(response)


class CancelOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # Check order belongs to user
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # Check admin setting (global)
        from admin_panel.models import SiteSettings
        settings = SiteSettings.objects.first()
        if not settings or not settings.allow_order_cancel:
            return Response({"error": "Order cancellation is disabled"}, status=403)

        # Check order status allowed for cancel
        if order.status not in ["PENDING", "PROCESSING"]:
            return Response({"error": "This order cannot be cancelled now"}, status=400)

        # Update status
        order.status = "CANCELLED"
        order.save()

        # Restore stock
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save()

        return Response({"message": "Order cancelled successfully"}, status=200)


class RequestReturnAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # Check order belongs to user
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # Check admin setting
        from admin_panel.models import SiteSettings
        settings = SiteSettings.objects.first()
        if not settings or not settings.allow_order_return:
            return Response({"error": "Returns are disabled"}, status=403)

        # Check return eligibility
        if order.status != "DELIVERED":
            return Response({"error": "Only delivered orders can be returned"}, status=400)

        # Check if return already requested
        if ReturnRequest.objects.filter(order=order, user=request.user).exists():
            return Response({"error": "Return already requested"}, status=400)

        # Create return request
        reason = request.data.get("reason", "")
        if not reason:
            return Response({"error": "Reason is required"}, status=400)

        ReturnRequest.objects.create(order=order, user=request.user, reason=reason)

        return Response({"message": "Return request submitted"}, status=201)




class OrderInvoiceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # Generate invoice PDF
        file_path = generate_invoice_pdf(order)

        # Return file as response
        return FileResponse(open(file_path, "rb"), content_type='application/pdf')

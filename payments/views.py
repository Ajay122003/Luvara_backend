from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from orders.models import Order
from .razorpay_client import razorpay_client
import razorpay
from rest_framework import status

class CreateRazorpayOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Invalid order"}, status=404)

        # Amount in paise
        amount_paise = int(order.total_amount * 100)

        razorpay_order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })

        order.payment_id = razorpay_order["id"]
        order.save()

        return Response({
            "order_id": order.id,
            "razorpay_order_id": razorpay_order["id"],
            "amount": amount_paise,
            "currency": "INR",
            "key": settings.RAZORPAY_KEY_ID
        })




class VerifyPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        data = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        }

        # Verify
        try:
            razorpay_client.utility.verify_payment_signature(data)
        except razorpay.errors.SignatureVerificationError:
            return Response({"error": "Payment verification failed"}, status=400)

        # Update order status
        try:
            order = Order.objects.get(payment_id=razorpay_order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        order.payment_status = "PAID"
        order.save()

        return Response({"message": "Payment successful"})

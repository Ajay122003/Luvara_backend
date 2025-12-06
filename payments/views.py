from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings

from .razorpay_client import razorpay_client
from .serializers import CreateRazorpayOrderSerializer, VerifyPaymentSerializer
from orders.models import Order
import razorpay


class CreateRazorpayOrderAPIView(APIView):
    """
    Step 1: Create Razorpay Order for an existing Order
    POST /api/payments/create/
    Body: { "order_id": 12 }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateRazorpayOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        order_id = serializer.validated_data["order_id"]

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.payment_status == "PAID":
            return Response({"error": "Order already paid"}, status=400)

        # amount in paise
        amount_paise = int(order.total_amount * 100)

        # Create Razorpay order
        razorpay_order = razorpay_client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1,  # Auto capture
            }
        )

       
        # We store Razorpay ORDER ID in Order.payment_id field
        order.payment_id = razorpay_order["id"]
        order.save()

        return Response(
            {
                "message": "Razorpay order created",
                "order_id": order.id,
                "order_number": order.order_number,
                "amount": amount_paise,
                "currency": "INR",
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "user_name": request.user.email,
            },
            status=200,
        )


class VerifyRazorpayPaymentAPIView(APIView):
    """
    Step 2: Verify Razorpay payment after success
    POST /api/payments/verify/
    Body:
    {
      "order_id": 12,
      "razorpay_order_id": "...",
      "razorpay_payment_id": "...",
      "razorpay_signature": "..."
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        try:
            order = Order.objects.get(id=data["order_id"], user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # Check razorpay_order_id matches what we stored
        if order.payment_id != data["razorpay_order_id"]:
            return Response(
                {"error": "Mismatched Razorpay order ID"}, status=400
            )

        payload = {
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        }

        # Signature verify
        try:
            razorpay_client.utility.verify_payment_signature(payload)
        except razorpay.errors.SignatureVerificationError:
            order.payment_status = "FAILED"
            order.save()
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If success
        order.payment_status = "PAID"
        # If you want, you can create separate fields for storing payment_id
        # For now we keep payment_id as the Razorpay order id (already stored)
        order.save()

        return Response(
            {
                "message": "Payment verified successfully",
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_status": order.payment_status,
            },
            status=200,
        )

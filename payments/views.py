import razorpay
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
import hmac
import hashlib
from .razorpay_client import razorpay_client
from .serializers import CreateRazorpayOrderSerializer, VerifyPaymentSerializer
from orders.models import Order



class CreateRazorpayOrderAPIView(APIView):
    """
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

        # ❌ Block COD orders
        if order.payment_method == "COD":
            return Response(
                {"error": "COD orders do not require online payment"},
                status=400
            )

        # ❌ Already paid
        if order.payment_status == "PAID":
            return Response({"error": "Order already paid"}, status=400)

        amount_paise = int(order.total_amount * 100)

        try:
            razorpay_order = razorpay_client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1,
            })
        except Exception as e:
            return Response(
                {"error": "Razorpay authentication failed"},
                status=500
            )

        order.payment_id = razorpay_order["id"]
        order.save(update_fields=["payment_id"])

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
    POST /api/payments/verify/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        try:
            order = Order.objects.get(
                id=data["order_id"],
                user=request.user
            )
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        # ❌ Block COD
        if order.payment_method == "COD":
            return Response(
                {"error": "COD orders do not require verification"},
                status=400
            )

        if order.payment_id != data["razorpay_order_id"]:
            return Response(
                {"error": "Mismatched Razorpay order ID"},
                status=400
            )

        payload = {
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        }

        try:
            razorpay_client.utility.verify_payment_signature(payload)
        except razorpay.errors.SignatureVerificationError:
            order.payment_status = "FAILED"
            order.save(update_fields=["payment_status"])
            return Response(
                {"error": "Payment verification failed"},
                status=400
            )

        order.payment_status = "PAID"
        order.save(update_fields=["payment_status"])

        return Response(
            {
                "message": "Payment verified successfully",
                "order_id": order.id,
                "order_number": order.order_number,
                "payment_status": order.payment_status,
            },
            status=200,
        )


class RazorpayWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.body
        received_signature = request.headers.get(
            "X-Razorpay-Signature"
        )

        expected_signature = hmac.new(
            key=bytes(settings.RAZORPAY_WEBHOOK_SECRET, "utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if received_signature != expected_signature:
            return Response({"error": "Invalid signature"}, status=400)

        data = request.data
        event = data.get("event")

        if event in ["payment.captured", "payment.failed"]:
            payment = data["payload"]["payment"]["entity"]
            razorpay_order_id = payment["order_id"]

            try:
                order = Order.objects.get(payment_id=razorpay_order_id)

                # ❌ Ignore COD orders
                if order.payment_method == "COD":
                    return Response({"status": "ignored"})

                order.payment_status = (
                    "PAID" if event == "payment.captured" else "FAILED"
                )
                order.save(update_fields=["payment_status"])

            except Order.DoesNotExist:
                pass

        return Response({"status": "ok"})

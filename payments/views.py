
import hmac
import hashlib
import base64
import json
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from cart.models import CartItem
from cashfree_pg.models.order_meta import OrderMeta
from cashfree_pg.api_client import Cashfree
from cashfree_pg.models.create_order_request import CreateOrderRequest
from cashfree_pg.models.customer_details import CustomerDetails

from .serializers import  VerifyPaymentSerializer
from orders.models import Order
from orders.serializers import *
from orders.utils import (
    send_order_invoice_email,
    send_admin_new_order_alert,
)
from orders.utils_invoice import generate_invoice_pdf


from products.models import ProductVariant
from .models import PendingOrder
from orders.utils import generate_order_number
from addresses.models import Address



def get_cashfree_client():
    if settings.CASHFREE_ENVIRONMENT.lower() == "production":
        env = Cashfree.PRODUCTION
    else:
        env = Cashfree.SANDBOX

    return Cashfree(
        XClientId=settings.CASHFREE_CLIENT_ID,
        XClientSecret=settings.CASHFREE_CLIENT_SECRET,
        XEnvironment=env
    )


    

# # =========================================================
# # CREATE CASHFREE ORDER
# # =========================================================

class CreateCashfreeOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            user = request.user
            

            print(" CREATE ORDER START")

            data = request.data.copy()


            address = Address.objects.filter(user=user, is_default=True).first()
            if not address:
               address = Address.objects.filter(user=user).last()

            data["payment_method"] = "ONLINE"
            data["address_id"] = address.id   #  IMPORTANT

            serializer = OrderCreateSerializer(
    data=data,
    context={"request": request}
)

            if not serializer.is_valid():
                print(" SERIALIZER ERROR:", serializer.errors)
                return Response(serializer.errors, status=400)

            data = serializer.validated_data

            print(" SERIALIZER DATA:", data)

            order_number = generate_order_number()
            total_amount = round(float(data["total"]), 2)
            customer = CustomerDetails(
                customer_id=f"user_{user.id}",
                customer_name=user.username,
                customer_email=user.email,
                customer_phone=data["address_obj"].phone
            )

            order_meta = OrderMeta(
                # return_url="http://localhost:3000/payment-success?order_id={order_id}"
                 return_url="https://luvarastore.com/payment-success?order_id={order_id}"
            )

            order_request = CreateOrderRequest(
                order_id=order_number,
                order_amount=total_amount,
                order_currency="INR",
                customer_details=customer,
                order_meta=order_meta
            )

            cashfree = get_cashfree_client()

            response = cashfree.PGCreateOrder(
                x_api_version="2023-08-01",
                create_order_request=order_request
            )

            print(" CASHFREE RESPONSE:", response.data)

            # SAVE PENDING
            PendingOrder.objects.create(
                user=user,
                order_number=order_number,
                cart_data=[
                    {
                        "variant_id": item.variant.id,
                        "quantity": item.quantity
                    }
                    for item in data["cart_items"]
                ],
                subtotal=data["subtotal"],
                discount=data["discount"],
                shipping=data["shipping_amount"],
                gst=data["gst_amount"],
                total=data["total"],
                address_id=data["address_obj"].id
            )

            print(" PENDING ORDER SAVED")

            return Response({
                "order_number": order_number,
                "payment_session_id": response.data.payment_session_id,
                "cf_order_id": response.data.cf_order_id
            })

        except Exception as e:
            print(" CREATE ORDER ERROR:", str(e))
            return Response({"error": str(e)}, status=500)
        

# # =========================================================
# # VERIFY PAYMENT (BACKUP)
# # =========================================================

class VerifyCashfreePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            print(" VERIFY START")

            serializer = VerifyPaymentSerializer(data=request.data)

            if not serializer.is_valid():
                print(" VERIFY SERIALIZER ERROR:", serializer.errors)
                return Response(serializer.errors, status=400)

            order_number = serializer.validated_data["order_id"]
            print(" VERIFY ORDER:", order_number)

            cashfree = get_cashfree_client()

            response = cashfree.PGFetchOrder(
                x_api_version="2023-08-01",
                order_id=order_number
            )

            print(" CASHFREE STATUS:", response.data.order_status)

        except Exception as e:
            print(" VERIFY ERROR:", str(e))
            return Response({"payment_status": "PENDING"})

        if response.data.order_status == "PAID":

            if Order.objects.filter(order_number=order_number).exists():
                print(" ALREADY CREATED")
                return Response({"payment_status": "PAID"})

            pending = PendingOrder.objects.get(order_number=order_number)
            print(" PENDING DATA:", pending.__dict__)

            user = pending.user

            order = Order.objects.create(
                user=user,
                order_number=order_number,

                subtotal_amount=pending.subtotal,
                discount_amount=pending.discount,
                shipping_amount=pending.shipping,
                gst_amount=pending.gst,
                total_amount=pending.total,

                address_id=pending.address_id,

                payment_method="ONLINE",
                payment_status="PAID"
            )

            print(" ORDER CREATED:", order.id)

            for item in pending.cart_data:
                variant = ProductVariant.objects.get(id=item["variant_id"])

                unit_price = variant.product.get_effective_price()

                order.items.create(
                    variant=variant,
                    quantity=item["quantity"],
                    original_price=variant.product.price,
                    unit_price=unit_price,
                    total_price=unit_price * item["quantity"],
                    color=variant.color or ""
                )

                variant.stock -= item["quantity"]
                variant.save()

            CartItem.objects.filter(user=user).delete()

            print(" CART CLEARED")

            pdf_path = generate_invoice_pdf(order)
            send_order_invoice_email(order, pdf_path)
            send_admin_new_order_alert(order)

            print(" EMAIL SENT")

            pending.delete()

            return Response({
                "message": "Order created successfully",
                "order_id": order.id,
                "order_number": order.order_number,

                "subtotal": float(order.subtotal_amount),
                "discount": float(order.discount_amount),
                "shipping": float(order.shipping_amount),
                "gst_percentage": float(order.gst_percentage),
                "gst_amount": float(order.gst_amount),
                "total_amount": float(order.total_amount),

                "payment_method": "ONLINE",
                "payment_status": order.payment_status,
                "coupon_code": None,
            }, status=201)

        elif response.data.order_status in ["ACTIVE", "PENDING"]:
            print(" PAYMENT STILL PENDING")
            return Response({"payment_status": "PENDING"})

        else:
            print(" PAYMENT FAILED")
            PendingOrder.objects.filter(order_number=order_number).delete()
            return Response({"payment_status": "FAILED"})
        

# # =========================================================
# # WEBHOOK (PRIMARY SOURCE )
# # =========================================================

class CashfreeWebhookAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def post(self, request):
        try:
            print(" WEBHOOK HIT")

            payload = request.body
            received_signature = request.headers.get("x-webhook-signature")

            generated_signature = base64.b64encode(
                hmac.new(
                    settings.CASHFREE_CLIENT_SECRET.encode(),
                    payload,
                    hashlib.sha256
                ).digest()
            ).decode()

            if received_signature != generated_signature:
                print(" INVALID SIGNATURE")
                return Response({"error": "Invalid signature"}, status=400)

            data = json.loads(payload)
            event = data.get("type")

            print(" EVENT:", event)

            if event in ["PAYMENT_SUCCESS_WEBHOOK", "PAYMENT_FAILED_WEBHOOK"]:

                payment = data["data"]["payment"]
                order_data = data["data"]["order"]

                order_number = order_data["order_id"]

                print(" ORDER:", order_number)

                if payment["payment_status"] == "SUCCESS":

                    if Order.objects.filter(order_number=order_number).exists():
                        print(" ALREADY CREATED")
                        return Response({"status": "already processed"})

                    pending = PendingOrder.objects.get(order_number=order_number)
                    user = pending.user

                    order = Order.objects.create(
                        user=user,
                        order_number=order_number,

                        subtotal_amount=pending.subtotal,
                        discount_amount=pending.discount,
                        shipping_amount=pending.shipping,
                        gst_amount=pending.gst,
                        total_amount=pending.total,

                        address_id=pending.address_id,

                        payment_method="ONLINE",
                        payment_status="PAID"
                    )

                    print(" ORDER CREATED VIA WEBHOOK")

                    pending.delete()

                else:
                    print(" PAYMENT FAILED")
                    PendingOrder.objects.filter(order_number=order_number).delete()

            return Response({"status": "ok"})

        except Exception as e:
            print(" WEBHOOK ERROR:", str(e))
            return Response({"error": str(e)}, status=500)


















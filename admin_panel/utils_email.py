from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.conf import settings
import random
import logging

logger = logging.getLogger(__name__)

# =========================
# OTP GENERATOR
# =========================
def generate_otp():
    return str(random.randint(100000, 999999))


# =========================
# ADMIN OTP EMAIL
# =========================
def send_admin_otp_email(admin_user, otp):
    subject = "Luvara Admin Login OTP"
    text_message = f"Your OTP is: {otp}"
    logo_url = "https://i.postimg.cc/9w73g34h/logo.png"

    html_message = f"""
    <div style="background:#f4f4f4; padding:40px 0; font-family:'Segoe UI', sans-serif;">
      <div style="max-width:520px; margin:auto; background:#ffffff;
                  padding:35px; border-radius:14px;
                  box-shadow:0 8px 30px rgba(0,0,0,0.08);">

        <div style="text-align:center; margin-bottom:20px;">
          <img src="{logo_url}" width="110" alt="Luvara Store"/>
        </div>

        <h1 style="text-align:center; letter-spacing:2px;">LUVARA ADMIN</h1>
        <p style="text-align:center; color:#777;">Secure Login Verification</p>

        <p>Hello <b>{admin_user.email}</b>,</p>
        <p>Your admin login OTP is:</p>

        <div style="text-align:center; margin:30px 0;">
          <div style="background:#000; color:#fff;
                      font-size:32px; font-weight:800;
                      padding:15px 30px; border-radius:10px;
                      letter-spacing:8px;">
            {otp}
          </div>
        </div>

        <p>This OTP is valid for <b>5 minutes</b>.</p>

        <p style="font-size:12px; color:#aaa; text-align:center;">
          © 2025 Luvara Store
        </p>
      </div>
    </div>
    """

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        print("✅ ADMIN OTP MAIL SENT")
        return True

    except Exception as e:
        print("❌ ADMIN OTP MAIL ERROR:", e)
        logger.error(f"Admin OTP mail error: {e}")
        return False


# =========================
# ORDER STATUS UPDATE EMAIL
# =========================
def send_order_status_update_email(order):
    subject = f"Order Update - {order.order_number}"

    courier_block = ""
    if order.courier_name or order.tracking_id:
        courier_block = f"""
Courier Name : {order.courier_name or "Not assigned yet"}
Tracking ID  : {order.tracking_id or "Not available yet"}
"""

    message = f"""
Hi {order.user.email},

Your order status has been updated.

Order Number : {order.order_number}
Current Status: {order.status}

{courier_block}

Thank you for shopping with Luvara Store.
"""

    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[order.user.email],
        )
        email.send(fail_silently=False)

        print("✅ ORDER STATUS MAIL SENT")
        return True

    except Exception as e:
        print("❌ ORDER STATUS MAIL ERROR:", e)
        logger.error(f"Order mail error: {e}")
        return False

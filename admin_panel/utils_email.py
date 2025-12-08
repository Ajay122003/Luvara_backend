from django.core.mail import send_mail
from django.conf import settings
import random

def generate_otp():
    return str(random.randint(100000, 999999))

def send_admin_otp_email(admin_user, otp):
    subject = "Your Admin Login OTP"
    message = f"""
Hello {admin_user.email},

Your OTP for admin login is: {otp}

This OTP is valid for 5 minutes.

If you did not request this login, please secure your account immediately.

Regards,
{settings.DEFAULT_FROM_EMAIL}
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [admin_user.email],
        fail_silently=False,
    )

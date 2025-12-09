from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import random


def generate_otp():
    return str(random.randint(100000, 999999))


def send_admin_otp_email(admin_user, otp):
    subject = "🔐 Your Admin Login OTP"

    text_message = f"Your OTP is: {otp}"

    html_message = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background: #f8f9fa;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 25px; 
                    border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
            
            <h2 style="text-align:center; color:#333;">Admin Login Verification</h2>
            <p style="font-size:15px; color:#555;">
                Hello {admin_user.email},<br><br>
                Your One-Time Password (OTP) for admin login is:
            </p>

            <div style="text-align:center; margin: 25px 0;">
                <span style="font-size:28px; letter-spacing: 4px; font-weight: bold; 
                             color: #d6336c; padding: 10px 20px; border: 2px dashed #d6336c;
                             display:inline-block; border-radius: 8px;">
                    {otp}
                </span>
            </div>

            <p style="font-size:14px; color:#777;">
                This OTP is valid for <b>5 minutes</b>.<br>
                If you did not request this login, please secure your account immediately.
            </p>

            <p style="font-size:12px; color:#aaa; text-align:center; margin-top: 30px;">
                © {settings.DEFAULT_FROM_EMAIL} • Admin Security
            </p>
        </div>
    </div>
    """

    email = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [admin_user.email],
    )
    email.attach_alternative(html_message, "text/html")
    email.send(fail_silently=False)

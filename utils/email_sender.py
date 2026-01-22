from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import random
import threading

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = "Your Luvara OTP Verification Code"
    text_message = f"Your OTP is: {otp} (valid for 5 minutes)"

    html_message = f"""
    <html>
      <body>
        <h2>Luvara OTP</h2>
        <p>Your OTP is <b>{otp}</b></p>
      </body>
    </html>
    """

    email_message = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send(fail_silently=True)


def send_otp_email_async(email, otp):
    threading.Thread(
        target=send_otp_email,
        args=(email, otp),
        daemon=True
    ).start()

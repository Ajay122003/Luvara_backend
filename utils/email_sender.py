from django.core.mail import send_mail
import random
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    subject = "Your Email Verification OTP"
    message = f"Your OTP is: {otp}. Valid for 5 minutes."
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,  
        [email],
        fail_silently=False,
    )

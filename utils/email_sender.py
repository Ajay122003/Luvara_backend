from django.core.mail import EmailMultiAlternatives
import random
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = " Your OTP Verification Code"
    
    text_message = f"Your OTP is: {otp}"

    html_message = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background: #f8f9fa;">
        <div style="max-width: 500px; margin: auto; background: white; padding: 25px; 
                    border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            
            <h2 style="text-align:center; color:#333;"> Email Verification</h2>
            <p style="font-size:16px; color:#555;">
                Hello,<br><br>
                Thank you for registering with us!<br>
                Please use the following One-Time Password (OTP) to verify your email:
            </p>

            <div style="text-align:center; margin: 30px 0;">
                <span style="font-size:32px; letter-spacing: 4px; font-weight: bold; 
                             color: #2b8a3e; padding: 10px 20px; border: 2px dashed #2b8a3e;
                             display:inline-block; border-radius: 8px;">
                    {otp}
                </span>
            </div>

            <p style="font-size:15px; color:#777;">
                This OTP is valid for <b>5 minutes</b>.  
                If you did not request this, please ignore this email.
            </p>

            <p style="font-size:14px; color:#aaa; text-align:center; margin-top: 30px;">
                © 2025 YourBrand • All Rights Reserved
            </p>
        </div>
    </div>
    """

    email_message = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )

    email_message.attach_alternative(html_message, "text/html")
    email_message.send()


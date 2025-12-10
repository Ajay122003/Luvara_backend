from django.core.mail import EmailMultiAlternatives
import random
from django.conf import settings


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = "Your Luvara OTP Verification Code"

    text_message = f"Your OTP is: {otp}"

    # --------------------------- HTML TEMPLATE ---------------------------
    html_message = f"""
    <div style="background:#f5f5f5; padding: 35px 0; font-family: 'Segoe UI', sans-serif;">
      <div style="max-width: 520px; margin: auto; background:#ffffff; border-radius: 15px; 
                  padding: 35px; box-shadow: 0 6px 25px rgba(0,0,0,0.08);">

        <!-- LOGO / BRAND -->
        <h1 style="text-align:center; margin-bottom: 10px; font-size:28px; 
                   letter-spacing: 2px; color:#000; font-weight:800;">
          LUVARA
        </h1>

        <p style="text-align:center; margin-top:-10px; margin-bottom:25px; 
                  color:#777; font-size:14px;">
          Fashion • Luxury • Elegance
        </p>

        <!-- HEADER -->
        <h2 style="text-align:center; color:#111; font-size:22px; font-weight:700;">
          Email Verification
        </h2>

        <p style="font-size:15px; color:#555; line-height:1.7; margin-top:20px;">
          Hello,<br><br>
          Welcome to <b>Luvara</b>! To complete your registration and secure your account,  
          please use the verification code below:
        </p>

        <!-- OTP BOX -->
        <div style="text-align:center; margin:35px 0;">
          <span style="
            font-size:36px; 
            font-weight:700;
            letter-spacing: 10px;
            color:#000;
            padding: 15px 25px;
            border-radius:12px;
            display:inline-block;
            background:#f2f2f2;
            border:2px solid #000;
          ">
            {otp}
          </span>
        </div>

        <p style="font-size:14px; color:#666; line-height:1.7;">
          This code is valid for <b>5 minutes</b>.<br>
          If you didn’t request this email, you can safely ignore it.
        </p>

        <!-- FOOTER -->
        <div style="margin-top:40px; text-align:center;">
          <p style="color:#aaa; font-size:13px; margin-bottom:5px;">
            © 2025 Luvara Store — All Rights Reserved
          </p>
          <p style="color:#bbb; font-size:12px;">
            This is an automated message. Please do not reply.
          </p>
        </div>

      </div>
    </div>
    """
    # --------------------------------------------------------------------

    email_message = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )

    email_message.attach_alternative(html_message, "text/html")
    email_message.send()

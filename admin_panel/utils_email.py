from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import random


def generate_otp():
    return str(random.randint(100000, 999999))


def send_admin_otp_email(admin_user, otp):
    subject = "Luvara Admin Login OTP"

    text_message = f"Your OTP is: {otp}"

    logo_url = "https://i.postimg.cc/9w73g34h/logo.png"

    html_message = f"""
    <div style="background:#f4f4f4; padding:40px 0; font-family:'Segoe UI', sans-serif;">
      <div style="
          max-width:520px; 
          margin:auto; 
          background:#ffffff; 
          padding:35px; 
          border-radius:14px; 
          box-shadow:0 8px 30px rgba(0,0,0,0.08);
      ">

        <!-- LOGO -->
        <div style="text-align:center; margin-bottom:20px;">
          <img src="{logo_url}" 
               alt="Luvara Store" 
               width="110"
               style="display:block; margin:auto;" />
        </div>

        <!-- BRAND -->
        <h1 style="
            text-align:center; 
            font-size:26px; 
            font-weight:800; 
            letter-spacing:2px; 
            color:#000;
            margin-bottom:5px;
        ">
          LUVARA ADMIN
        </h1>

        <p style="
            text-align:center; 
            color:#777; 
            font-size:13px; 
            margin-top:-5px;
        ">
          Secure Login Verification
        </p>

        <!-- TITLE -->
        <h2 style="
            text-align:center; 
            margin:25px 0 10px; 
            font-size:20px; 
            color:#111; 
            font-weight:600;
        ">
          Your Login OTP Code
        </h2>

        <!-- MESSAGE -->
        <p style="font-size:15px; color:#444; line-height:1.7;">
          Hello <b>{admin_user.email}</b>,<br>
          To proceed with your admin login, please use the secure One-Time Password (OTP provided below).
        </p>

        <!-- OTP BOX -->
        <div style="text-align:center; margin:35px 0;">
          <div style="
              display:inline-block;
              background:#000;
              padding:18px 28px;
              border-radius:12px;
              color:#fff;
              font-weight:800;
              font-size:34px;
              letter-spacing:10px;
              border:2px solid #000;
          ">
            {otp}
          </div>
        </div>

        <!-- INFO -->
        <p style="font-size:14px; color:#666; line-height:1.6;">
          This OTP is valid for <b>5 minutes</b>.<br>
          If you did not request this login attempt, please change your admin password immediately.
        </p>

        <!-- FOOTER -->
        <div style="text-align:center; margin-top:40px;">
          <p style="font-size:12px; color:#aaa; margin-bottom:5px;">
            © 2025 Luvara Store • Admin Security System
          </p>
          <p style="font-size:11px; color:#bbb;">
            This is an automated security alert. Do not reply to this email.
          </p>
        </div>

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

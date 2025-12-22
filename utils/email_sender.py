from django.core.mail import EmailMultiAlternatives
import random
from django.conf import settings

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    subject = "Your Luvara OTP Verification Code"
    
    text_message = f"Your OTP is: {otp} (valid for 5 minutes)"
    
    logo_url = "https://i.postimg.cc/gjMYJmmn/Logo.png"  # Replace with your actual logo URL
    
    html_message = f"""
    <html>
    <body style="margin:0; padding:0; font-family: 'Segoe UI', sans-serif; background:#f5f5f5;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td align="center">
            <table width="520" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:15px; padding:35px; box-shadow:0 6px 25px rgba(0,0,0,0.08);">
              
              <!-- LOGO -->
              <tr>
                <td align="center" style="padding-bottom: 20px;">
                  <img src="{logo_url}" alt="Luvara Store" width="120" style="display:block;" />
                </td>
              </tr>
              
              <!-- HEADER -->
              <tr>
                <td align="center">
                  <h2 style="color:#111; font-size:22px; font-weight:700; margin:0;">Email Verification</h2>
                  <p style="font-size:14px; color:#777; margin:5px 0 20px 0;">Fashion • Luxury • Elegance</p>
                </td>
              </tr>
              
              <!-- BODY -->
              <tr>
                <td>
                  <p style="font-size:15px; color:#555; line-height:1.7;">
                    Hello,<br><br>
                    Welcome to <b>Luvara</b>! To complete your registration and secure your account, please use the verification code below:
                  </p>
                </td>
              </tr>
              
              <!-- OTP -->
              <tr>
                <td align="center" style="padding: 25px 0;">
                  <span style="
                    font-size:36px;
                    font-weight:700;
                    letter-spacing:10px;
                    color:#000;
                    padding:15px 25px;
                    border-radius:12px;
                    display:inline-block;
                    background:#f2f2f2;
                    border:2px solid #000;
                  ">{otp}</span>
                </td>
              </tr>
              
              <!-- FOOTER -->
              <tr>
                <td>
                  <p style="font-size:14px; color:#666; line-height:1.7;">
                    This code is valid for <b>5 minutes</b>.<br>
                    If you didn’t request this email, you can safely ignore it.
                  </p>
                  <hr style="border:none; border-top:1px solid #eee; margin:20px 0;">
                  <p style="text-align:center; font-size:12px; color:#aaa;">
                    © 2025 Luvara Store — All Rights Reserved<br>
                    This is an automated message. Please do not reply.
                  </p>
                </td>
              </tr>
              
            </table>
          </td>
        </tr>
      </table>
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
    email_message.send()

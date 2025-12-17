import random
import string
from django.core.mail import EmailMessage
from django.conf import settings


# -------------------------------
# Generate Order Number
# Example: ODR83920147
# -------------------------------
def generate_order_number():
    return "ODR" + "".join(random.choices(string.digits, k=8))


# -------------------------------
# Send Invoice Email (with GST info)
# -------------------------------
def send_order_invoice_email(order, pdf_path):
    subject = f"Invoice for your Order {order.order_number}"

    message = f"""
Hi {order.user.email},

Thank you for shopping with us! 🛍️

We have successfully received your order.

📦 Order Number: {order.order_number}

💰 Price Summary:
Subtotal      : ₹{order.subtotal_amount}
Discount      : -₹{order.discount_amount}
GST ({order.gst_percentage}%): ₹{order.gst_amount}
-------------------------------
Total Payable : ₹{order.total_amount}

Your invoice is attached with this email as a PDF.

If you have any questions, feel free to contact our support team.

Warm regards,
Luvara Store
{settings.DEFAULT_FROM_EMAIL}
"""

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.user.email],
    )

    # Attach invoice PDF
    if pdf_path:
        email.attach_file(pdf_path)

    # Send email
    email.send(fail_silently=False)

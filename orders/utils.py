import random
import string
from django.core.mail import EmailMessage
from django.conf import settings


def generate_order_number():
    # Example: ODR12345678
    return "ODR" + "".join(random.choices(string.digits, k=8))


def send_order_invoice_email(order, pdf_path):
    subject = f"Your Invoice for Order {order.order_number}"

    message = f"""
Hi {order.user.email},

Thank you for shopping with us!

Your order {order.order_number} has been received successfully.

Please find the attached invoice PDF for your order.

Regards,
{settings.DEFAULT_FROM_EMAIL}
"""

    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
    )

    email.attach_file(pdf_path)
    email.send(fail_silently=False)

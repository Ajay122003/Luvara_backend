from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os


def generate_invoice_pdf(order):
    file_name = f"invoice_{order.order_number}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, "invoices", file_name)

    # Create folder if not exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    y = height - 40

    # ---- HEADER ----
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, y, "ORDER INVOICE")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(30, y, f"Order Number: {order.order_number}")
    y -= 20

    c.drawString(30, y, f"Order Date: {order.created_at.strftime('%d-%m-%Y')}")
    y -= 30

    # ---- BILLING ADDRESS ----
    address = order.address
    if address:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, y, "Billing Address:")
        y -= 20

        c.setFont("Helvetica", 12)
        c.drawString(30, y, f"{address.name}")
        y -= 18
        c.drawString(30, y, f"{address.phone}")
        y -= 18
        c.drawString(30, y, f"{address.full_address}")
        y -= 18
        c.drawString(30, y, f"{address.city}, {address.state}")
        y -= 18
        c.drawString(30, y, f"Pincode: {address.pincode}")
        y -= 40

    # ---- ORDER ITEMS ----
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "Items:")
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, y, "Product")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Price")
    c.drawString(380, y, "Total")
    y -= 20

    c.setFont("Helvetica", 12)

    for item in order.items.all():
        total = item.price * item.quantity

        c.drawString(30, y, (item.product.name[:25] if item.product else "N/A"))
        c.drawString(250, y, str(item.quantity))
        c.drawString(300, y, f"{item.price}")
        c.drawString(380, y, f"{total}")

        y -= 20

        if y < 100:
            c.showPage()
            y = height - 100

    # ---- PRICE SUMMARY ----
    y -= 20
    c.setFont("Helvetica-Bold", 12)

    subtotal = order.total_amount + order.discount_amount

    c.drawString(300, y, "Subtotal:")
    c.drawString(380, y, f"{subtotal}")
    y -= 20

    c.drawString(300, y, "Discount:")
    c.drawString(380, y, f"-{order.discount_amount}")
    y -= 20

    c.drawString(300, y, "Final Total:")
    c.drawString(380, y, f"{order.total_amount}")
    y -= 40

    # ---- FOOTER ----
    c.setFont("Helvetica-Oblique", 11)
    c.drawString(30, y, "Thank you for shopping with us!")

    c.save()
    return file_path

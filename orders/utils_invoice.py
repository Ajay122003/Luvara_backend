from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.conf import settings
import os


def generate_invoice_pdf(order):
    file_name = f"invoice_{order.order_number}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, "invoices", file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - 40

    # ================= HEADER =================
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, y, "ORDER INVOICE")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(30, y, f"Order Number: {order.order_number}")
    y -= 20
    c.drawString(30, y, f"Order Date: {order.created_at.strftime('%d-%m-%Y')}")
    y -= 30

    # ================= BILLING / DELIVERY ADDRESS =================
    address = order.address
    if address:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, y, "Delivery Address:")
        y -= 20

        c.setFont("Helvetica", 12)
        c.drawString(30, y, address.name)
        y -= 18
        c.drawString(30, y, address.phone)
        y -= 18
        c.drawString(30, y, address.full_address)
        y -= 18
        c.drawString(30, y, f"{address.city}, {address.state}")
        y -= 18
        c.drawString(30, y, f"Pincode: {address.pincode}")
        y -= 40

    # ================= ORDER ITEMS =================
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30, y, "Items:")
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, y, "Product")
    c.drawString(240, y, "Qty")
    c.drawString(290, y, "Unit Price")
    c.drawString(380, y, "Total")
    y -= 20

    c.setFont("Helvetica", 12)

    for item in order.items.all():
        # 🔥 SAFE PRICE FETCH (NO CRASH)
        unit_price = (
            getattr(item, "unit_price", None)
            or getattr(item, "original_price", None)
            or 0
        )

        total = unit_price * item.quantity

        product_name = (
            item.variant.product.name
            if item.variant and item.variant.product
            else "N/A"
        )

        c.drawString(30, y, product_name[:30])
        c.drawString(240, y, str(item.quantity))
        c.drawString(290, y, f"₹{unit_price}")
        c.drawString(380, y, f"₹{total}")

        y -= 20
        if y < 100:
            c.showPage()
            y = height - 100
            c.setFont("Helvetica", 12)

    # ================= PRICE SUMMARY =================
    y -= 30
    c.setFont("Helvetica-Bold", 12)

    c.drawString(300, y, "Subtotal:")
    c.drawString(380, y, f"₹{order.subtotal_amount}")
    y -= 20

    c.drawString(300, y, "Discount:")
    c.drawString(380, y, f"-₹{order.discount_amount}")
    y -= 20

    c.drawString(300, y, "Shipping:")
    c.drawString(380, y, f"₹{order.shipping_amount}")
    y -= 20

    taxable_amount = (
        order.subtotal_amount
        - order.discount_amount
        + order.shipping_amount
    )

    c.drawString(300, y, "Taxable Amount:")
    c.drawString(380, y, f"₹{taxable_amount}")
    y -= 20

    c.drawString(300, y, f"GST ({order.gst_percentage}%):")
    c.drawString(380, y, f"₹{order.gst_amount}")
    y -= 20

    c.drawString(300, y, "Final Total:")
    c.drawString(380, y, f"₹{order.total_amount}")
    y -= 40

    # ================= FOOTER =================
    c.setFont("Helvetica-Oblique", 11)
    c.drawString(30, y, "Thank you for shopping with us!")

    c.save()
    return file_path

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from django.conf import settings
import os


def generate_invoice_pdf(order):
    file_name = f"invoice_{order.order_number}.pdf"
    file_path = os.path.join(settings.MEDIA_ROOT, "invoices", file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    # ================= HEADER =================
    elements.append(Paragraph("<b>ORDER INVOICE</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Order Number: {order.order_number}", styles["Normal"]))
    elements.append(Paragraph(f"Order Date: {order.created_at.strftime('%d-%m-%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    # ================= ADDRESS =================
    address = order.address
    if address:
        elements.append(Paragraph("<b>Delivery Address</b>", styles["Heading3"]))
        elements.append(Spacer(1, 0.1 * inch))

        address_lines = [
            address.name,
            address.phone,
            address.full_address,
            f"{address.city}, {address.state}",
            f"Pincode: {address.pincode}",
        ]

        for line in address_lines:
            elements.append(Paragraph(line, styles["Normal"]))

        elements.append(Spacer(1, 0.4 * inch))

    # ================= ITEMS TABLE =================
    data = [
        ["Product", "Qty", "Unit Price", "Total"]
    ]

    for item in order.items.all():
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

        data.append([
            product_name,
            str(item.quantity),
            f"₹{unit_price}",
            f"₹{total}"
        ])

    table = Table(data, colWidths=[3 * inch, 0.7 * inch, 1 * inch, 1 * inch])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    # ================= SUMMARY TABLE =================
    taxable_amount = (
        order.subtotal_amount
        - order.discount_amount
        + order.shipping_amount
    )

    summary_data = [
        ["Subtotal", f"₹{order.subtotal_amount}"],
        ["Discount", f"-₹{order.discount_amount}"],
        ["Shipping", f"₹{order.shipping_amount}"],
        ["Taxable Amount", f"₹{taxable_amount}"],
        [f"GST ({order.gst_percentage}%)", f"₹{order.gst_amount}"],
        ["Final Total", f"₹{order.total_amount}"],
    ]

    summary_table = Table(summary_data, colWidths=[4 * inch, 1.5 * inch])

    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))

    # ================= FOOTER =================
    elements.append(Paragraph("Thank you for shopping with us!", styles["Italic"]))

    doc.build(elements)

    return file_path
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "total_amount", "payment_status", "status", "created_at")
    list_filter = ("payment_status", "status")
    inlines = [OrderItemInline]

admin.site.register(OrderItem)


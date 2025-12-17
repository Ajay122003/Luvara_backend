from django.contrib import admin
from .models import Product, ProductImage

class ImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price","sale_price", "sizes" , "stock", "is_active")

admin.site.register(ProductImage)

# @admin.register(ProductImage)
# class ProductImageAdmin(admin.ModelAdmin):
#     list_display = ("id", "product", "image")
from django.contrib import admin
from .models import Product, ProductImage, ProductVariant


# -------------------------
# PRODUCT IMAGE INLINE
# -------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


# -------------------------
# PRODUCT VARIANT INLINE
# -------------------------
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("size", "stock")


# -------------------------
# PRODUCT ADMIN
# -------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "sale_price",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active", "category")
    search_fields = ("name",)
    ordering = ("-id",)

    inlines = [
        ProductVariantInline,   # 
        ProductImageInline,     # 
    ]


# -------------------------
# PRODUCT IMAGE ADMIN
# -------------------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "image")


# -------------------------
# PRODUCT VARIANT ADMIN
# -------------------------
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "size", "stock")
    list_filter = ("size",)
    search_fields = ("product__name",)

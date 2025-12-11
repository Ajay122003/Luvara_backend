from rest_framework import serializers
from .models import Category
from products.models import Product
from products.serializers import ProductSerializer


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    products = serializers.SerializerMethodField(read_only=True)  # ✅ ADD THIS

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "image",
            "image_url",
            "is_active",
            "sort_order",
            "products",  # ✅ FRONTEND USES THIS
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_products(self, obj):
        # Only active products inside this category
        qs = Product.objects.filter(category=obj, is_active=True)

        return ProductSerializer(
            qs,
            many=True,
            context=self.context
        ).data


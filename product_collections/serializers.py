from rest_framework import serializers
from .models import Collection
from products.serializers import ProductSerializer


class CollectionListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "image_url",
            "is_active",
            "product_count",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_product_count(self, obj):
        # Efficient count query
        return obj.products.filter(is_active=True).count()


class CollectionDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()  # custom to optimize loading

    class Meta:
        model = Collection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "image_url",
            "is_active",
            "products",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_products(self, obj):
        from products.models import Product

        queryset = obj.products.filter(is_active=True).order_by("-id")
        serializer = ProductSerializer(
            queryset, many=True, context=self.context
        )
        return serializer.data

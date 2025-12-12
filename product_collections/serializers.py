from rest_framework import serializers
from .models import Collection
from products.models import Product
from products.serializers import ProductSerializer


# LIST SERIALIZER (ADMIN + FRONTEND)
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
            "sort_order",
            "product_count",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


# DETAIL SERIALIZER (USER SIDE)
class CollectionDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

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
            "sort_order",
            "products",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_products(self, obj):
        qs = obj.products.filter(is_active=True)
        return ProductSerializer(qs, many=True, context=self.context).data

class CollectionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = [
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "sort_order",
        ]
        extra_kwargs = {
            "slug": {"required": False},
        }

    def create(self, validated_data):
        return Collection.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

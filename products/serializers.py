from rest_framework import serializers
from .models import *
from categories.models import Category

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.url)


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "description",
            "price", "sale_price", "sizes", "colors",
            "stock", "category", "category_name",
            "images", "is_active", "created_at"
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )

    class Meta:
        model = Product
        fields = [
            "name", "description", "price", "sale_price",
            "sizes", "colors", "stock", "category", "images"
        ]

    def create(self, validated_data):
        images = validated_data.pop("images")
        product = Product.objects.create(**validated_data)

        for img in images:
            ProductImage.objects.create(product=product, image=img)

        return product

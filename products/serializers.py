from rest_framework import serializers
from .models import Product, ProductImage, ProductVariant
from product_collections.models import Collection
from offers.models import Offer
from django.utils import timezone


# --------------------------------------------------
# Product Image Serializer
# --------------------------------------------------
class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url


# --------------------------------------------------
# Product Variant Serializer
# --------------------------------------------------
class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = "__all__"
        extra_kwargs = {
            "color": {
                "required": False,
                "allow_null": True,
                "allow_blank": True
            }
        }


# --------------------------------------------------
# Product Read Serializer (USER SIDE)
# --------------------------------------------------
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    category_name = serializers.CharField(source="category.name", read_only=True)
    collection_names = serializers.SerializerMethodField()

    offer_title = serializers.CharField(
        source="offer.title",
        read_only=True
    )

    effective_price = serializers.SerializerMethodField()

    collections = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "description",
            "price",
            "sale_price",
            "effective_price",
            "offer",
            "offer_title",
            "colors",
            "category",
            "category_name",
            "collections",
            "collection_names",
            "variants",
            "images",
            "is_active",
            "created_at",
        ]

    def get_collection_names(self, obj):
        return [c.name for c in obj.collections.all()]

    def get_effective_price(self, obj):
        """
        Same logic as Product model
        """
        now = timezone.now()

        if (
            obj.offer
            and obj.offer.is_active
            and obj.offer.start_date <= now
            and obj.offer.end_date >= now
        ):
            if obj.offer.discount_type == "PERCENT":
                discount = (obj.offer.discount_value / 100) * obj.price
                return round(obj.price - discount, 2)

            if obj.offer.discount_type == "FLAT":
                return max(obj.price - obj.offer.discount_value, 0)

        if obj.sale_price:
            return float(obj.sale_price)

        return float(obj.price)


# --------------------------------------------------
# Product Create Serializer (ADMIN ADD PRODUCT)
# --------------------------------------------------
class ProductCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=True
    )

    variants = ProductVariantSerializer(
        many=True,
        write_only=True,
        required=True
    )

    collections = serializers.PrimaryKeyRelatedField(
        queryset=Collection.objects.all(),
        many=True,
        required=False
    )

    offer = serializers.PrimaryKeyRelatedField(
        queryset=Offer.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "description",
            "price",
            "sale_price",
            "offer",
            "colors",
            "category",
            "collections",
            "images",
            "variants",
        ]

    def create(self, validated_data):
        variants_data = validated_data.pop("variants")
        images = validated_data.pop("images")
        collections = validated_data.pop("collections", [])

        product = Product.objects.create(**validated_data)

        if collections:
            product.collections.set(collections)

        for variant in variants_data:
            ProductVariant.objects.create(
                product=product,
                size=variant["size"],
                color=variant.get("color"),
                stock=variant["stock"],
            )

        for img in images:
            ProductImage.objects.create(
                product=product,
                image=img
            )

        return product

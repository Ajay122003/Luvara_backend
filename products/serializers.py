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
# Product Read Serializer (USER SIDE + OFFER DETAIL)
# --------------------------------------------------
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    #  MAIN IMAGE (FOR OFFER / LIST PAGE)
    image_url = serializers.SerializerMethodField()

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    collection_names = serializers.SerializerMethodField()

    offer_title = serializers.CharField(
        source="offer.title",
        read_only=True
    )
    offer_end_date = serializers.DateTimeField(
        source="offer.end_date",
        read_only=True
    )

    offer_is_active = serializers.BooleanField(
        source="offer.is_active",
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
            "effective_price",   #  FINAL PRICE
            "image_url",         #  PRIMARY IMAGE
            "offer",
            "offer_title",
             "offer_end_date", 
             "offer_is_active",
            "colors",
            "category",
            "category_name",
            "collections",
            "collection_names",
            "variants",
            "images",            # full gallery
            "is_active",
            "created_at",
        ]

    # -----------------------------
    # FIRST IMAGE ONLY (SAFE)
    # -----------------------------
    def get_image_url(self, obj):
        request = self.context.get("request")
        image = obj.images.first()   #  FIRST IMAGE

        if image:
            if request:
                return request.build_absolute_uri(image.image.url)
            return image.image.url
        return None

    # -----------------------------
    # COLLECTION NAMES
    # -----------------------------
    def get_collection_names(self, obj):
        return [c.name for c in obj.collections.all()]

    # -----------------------------
    # EFFECTIVE PRICE (OFFER > SALE > PRICE)
    # -----------------------------
    def get_effective_price(self, obj):   #  obj MUST BE HERE
        now = timezone.now()

        #  OFFER PRICE
        if (
            obj.offer
            and obj.offer.is_active
            and obj.offer.start_date <= now
            and obj.offer.end_date >= now
        ):
            if obj.offer.discount_type == "PERCENT":
                discount = (obj.offer.discount_value / 100) * obj.price
                return round(obj.price - discount)

            if obj.offer.discount_type == "FLAT":
                return max(obj.price - obj.offer.discount_value, 0)

        #  SALE PRICE
        if obj.sale_price:
            return obj.sale_price

        #  NORMAL PRICE
        return obj.price



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

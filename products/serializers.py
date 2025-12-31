from rest_framework import serializers
from .models import Product, ProductImage, ProductVariant
from product_collections.models import Collection


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
# Product Variant Serializer (SIZE + COLOR + STOCK)
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
# Product Read Serializer (List / Detail)
# --------------------------------------------------
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)

    category_name = serializers.CharField(source="category.name", read_only=True)
    collection_names = serializers.SerializerMethodField()
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
        return float(obj.sale_price if obj.sale_price else obj.price)


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

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "description",
            "price",
            "sale_price",
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

        # Create product
        product = Product.objects.create(**validated_data)

        # Save collections
        if collections:
            product.collections.set(collections)

        # Save variants (SIZE + COLOR + STOCK)
        for variant in variants_data:
            ProductVariant.objects.create(
                product=product,
                size=variant["size"],
                color=variant["color"],
                stock=variant["stock"],
            )

        # Save images
        for img in images:
            ProductImage.objects.create(
                product=product,
                image=img
            )

        return product

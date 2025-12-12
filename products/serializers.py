from rest_framework import serializers
from .models import Product, ProductImage
from product_collections.models import Collection


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ["id", "image", "image_url"]

    def get_image_url(self, obj):
        request = self.context.get("request")

        # FIX: If request is None (like when used inside Cart), use static URL
        if request:
            return request.build_absolute_uri(obj.image.url)

        return obj.image.url  # fallback safe URL





class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    #  Correct way (NO source)
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
            "id", "name", "description",
            "price", "sale_price", "effective_price",
            "sizes", "colors",
            "stock", "category", "category_name",
            "collections",
            "collection_names",      
            "images",
            "is_active", "created_at",
        ]

    #  Returns names of all collections
    def get_collection_names(self, obj):
        return [c.name for c in obj.collections.all()]

    def get_effective_price(self, obj):
        return float(obj.sale_price if obj.sale_price else obj.price)


class ProductCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
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
            "name", "description", "price", "sale_price",
            "sizes", "colors", "stock",
            "category", "collections",
            "images",
        ]

    def create(self, validated_data):
    # REMOVE collections from validated_data
       validated_data.pop("collections", None)

       images = validated_data.pop("images", [])

       request = self.context.get("request")
       collections = request.data.getlist("collections")

    # Create product WITHOUT collections
       product = Product.objects.create(**validated_data)

    # Save images
       for img in images:
           ProductImage.objects.create(product=product, image=img)

    # Save M2M
       if collections:
          product.collections.set(collections)

       return product

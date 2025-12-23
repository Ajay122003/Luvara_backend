from rest_framework import serializers
from .models import Coupon
from django.utils import timezone


class AdminCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = "__all__"


class CouponApplySerializer(serializers.Serializer):
    code = serializers.CharField()
    amount = serializers.FloatField()

    def validate(self, data):
        code = data["code"]
        amount = data["amount"]

        try:
            coupon = Coupon.objects.get(code__iexact=code)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code")

        if not coupon.is_active:
            raise serializers.ValidationError("Coupon is not active")

        if timezone.now() > coupon.expiry_date:
            raise serializers.ValidationError("Coupon expired")

        if amount < coupon.min_purchase:
            raise serializers.ValidationError(
                f"Minimum purchase required: {coupon.min_purchase}"
            )

        if coupon.used_count >= coupon.usage_limit:
            raise serializers.ValidationError("Coupon usage limit exceeded")

        if coupon.discount_type == "PERCENT" and coupon.discount_value > 100:
            raise serializers.ValidationError("Invalid discount percentage")

        data["coupon"] = coupon
        return data

    def create(self, validated_data):
        coupon = validated_data["coupon"]
        amount = validated_data["amount"]

        # Calculate discount
        if coupon.discount_type == "PERCENT":
            discount = (coupon.discount_value / 100) * amount
        else:
            discount = min(coupon.discount_value, amount)

        # Apply max discount cap
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)

        final_amount = max(amount - discount, 0)

        # Increment usage count
        coupon.used_count += 1
        coupon.save(update_fields=["used_count"])

        return {
            "coupon": coupon.code,
            "discount": round(discount, 2),
            "final_amount": round(final_amount, 2),
        }


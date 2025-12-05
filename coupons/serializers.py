from rest_framework import serializers
from .models import Coupon
from django.utils.timezone import now

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

        if coupon.expiry_date < now():
            raise serializers.ValidationError("Coupon expired")

        if amount < coupon.min_purchase:
            raise serializers.ValidationError(
                f"Minimum purchase required: {coupon.min_purchase}"
            )

        data["coupon_obj"] = coupon
        return data

    def create(self, validated_data):
        coupon = validated_data["coupon_obj"]
        amount = validated_data["amount"]

        if coupon.discount_type == "PERCENT":
            discount = (coupon.discount_value / 100) * amount
        else:
            discount = coupon.discount_value

        final_amount = max(amount - discount, 0)

        return {
            "discount": round(discount, 2),
            "final_amount": round(final_amount, 2),
        }

from rest_framework import serializers


class CreateCashfreeOrderSerializer(serializers.Serializer):
    # order_id = serializers.IntegerField()
    pass


class VerifyPaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    # cf_order_id = serializers.CharField()
    # cf_payment_id = serializers.CharField()
    # payment_status = serializers.CharField()

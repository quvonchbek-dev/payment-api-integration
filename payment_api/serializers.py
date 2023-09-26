from rest_framework import serializers


class CheckPaymentSerializerUzum(serializers.Serializer):
    orderId = serializers.CharField()


class ClickPrepareSerializer(serializers.Serializer):
    click_trans_id = serializers.IntegerField()
    service_id = serializers.IntegerField()
    click_paydoc_id = serializers.IntegerField()
    merchant_trans_id = serializers.CharField()
    amount = serializers.FloatField(required=True)
    action = serializers.IntegerField(required=True)
    error = serializers.IntegerField()
    error_note = serializers.CharField()
    sign_time = serializers.CharField()
    sign_string = serializers.CharField(required=True)


class ClickCompleteSerializer(ClickPrepareSerializer):
    merchant_prepare_id = serializers.IntegerField(allow_null=True)


class PaymentSerializer(serializers.Serializer):
    transactionId = serializers.CharField()
    orderId = serializers.CharField()
    amount = serializers.IntegerField()

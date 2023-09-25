from rest_framework import serializers


class CheckPaymentSerializer(serializers.Serializer):
    orderId = serializers.CharField()


class PaymentSerializer(serializers.Serializer):
    transactionId = serializers.CharField()
    orderId = serializers.CharField()
    amount = serializers.IntegerField()
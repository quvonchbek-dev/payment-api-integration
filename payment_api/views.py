import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from payment_api.models import Order, Payment
from payment_api.serializers import CheckPaymentSerializer, PaymentSerializer


@api_view(['POST'])
def check_payment(request):
    serializer = CheckPaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    order_id = request.data.get('orderId')
    data = {
        "status": False,
        "error": "order_not_found",
        "data": None
    }
    try:
        order_qs = Order.objects.filter(pk=order_id)
    except Exception as ex:
        data["error"] = str(ex)
        return Response(data)
    if order_qs.exists():
        order = order_qs.first()

        if order.status == Order.Status.USED:
            data["error"] = "already_paid"
        elif order.status == Order.Status.EXPIRED:
            data["error"] = "order_expired"
        elif order.status == Order.Status.CANCELLED:
            data["error"] = "order_cancelled"
        else:
            now = timezone.now()
            if (order.created_at + datetime.timedelta(days=1)) < now:
                data["error"] = "order_expired"
                order.status = Order.Status.EXPIRED
                order.save()
            else:
                data = {
                    "status": True,
                    "error": None,
                    "data": {
                        "fio": order.owner.name,
                        "amount": order.amount
                    }
                }
    return Response(data)


@api_view(['POST'])
def process_payment(request):
    serializer = PaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    transaction_id = serializer.validated_data['transactionId']
    order_id = serializer.validated_data['orderId']
    amount = serializer.validated_data['amount']
    data = {"status": False, "error": ""}

    order_qs = Order.objects.filter(pk=order_id)
    if not order_qs.exists():
        data["error"] = "order_not_found"
        return Response(data)

    order = order_qs.first()
    if order.status == 0:
        now = timezone.now()
        if (order.created_at + datetime.timedelta(days=1)) < now:
            data["error"] = "order_expired"
            order.status = Order.Status.EXPIRED
            order.save()
        elif order.amount != amount:
            data["error"] = "incorrect_amount"
        elif data["error"] == "":
            try:
                Payment.objects.create(
                    order=order,
                    transactionId=transaction_id,
                )
                data["status"] = True
                order.status = Order.Status.USED
                order.save()
            except Exception as ex:
                data["error"] = str(ex)

            '''
            Shu yerda to'lov foydalanuvchi profiliga saqlanib, unga to'lov haqidagi xabar yuborilishi kerak.
            '''
    else:
        data["error"] = ["already_paid", "order_cancelled", "order_expired"][order.status - 1]
    return Response(data)
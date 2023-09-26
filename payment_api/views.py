import datetime
import os

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from payment_api.models import Order, Payment, ClickPayment
from payment_api.serializers import CheckPaymentSerializerUzum, PaymentSerializer, ClickCompleteSerializer, \
    ClickPrepareSerializer
from django.http import JsonResponse
import hashlib

"""
UUM
"""


@api_view(['POST'])
def check_payment(request):
    serializer = CheckPaymentSerializerUzum(data=request.data)
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

        if order.status == Order.Status.PAID:
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
                order.status = Order.Status.PAID
                order.save()
            except Exception as ex:
                data["error"] = str(ex)

            '''
            Shu yerda to'lov foydalanuvchi profiliga saqlanib, unga to'lov haqidagi xabar yuborilishi kerak.
            '''
    else:
        data["error"] = ["already_paid", "order_cancelled", "order_expired"][order.status - 1]
    return Response(data)


"""
CLICK API
"""
SECRET_KEY = os.getenv("CLICK_SECRET_KEY")


def check_signature(data):
    amount = data["amount"]
    if amount % 1 == 0:
        amount = int(amount)
    if data['action'] == 0:  # Prepare
        sign_string = (f"{data['click_trans_id']}{data['service_id']}{SECRET_KEY}{data['merchant_trans_id']}"
                       f"{int(amount)}{data['action']}{data['sign_time']}")
    elif data['action'] == 1:  # Complete
        sign_string = (f"{data['click_trans_id']}{data['service_id']}{SECRET_KEY}{data['merchant_trans_id']}"
                       f"{data['merchant_prepare_id']}{amount}{data['action']}{data['sign_time']}")
    else:
        return
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest()


CLICK_ERRORS = {
    0: "Success",
    -1: "SIGN CHECK FAILED!",
    -2: "Incorrect parameter amount",
    -3: "Action not found",
    -4: "Already paid",
    -5: "User does not exist",
    -6: "Transaction does not exist",
    -7: "Failed to update user",
    -8: "Error in request from click",
    -9: "Transaction cancelled",
}


def get_error_code(order: Order, data) -> int:
    if order is None:
        return -6
    if data["error"] < 0:
        order.status = Order.Status.CANCELLED
        order.save()
        return -9
    if order.amount != data["amount"]:
        return -2
    if order.status == Order.Status.PAID:
        return -4
    if order.status == Order.Status.CANCELLED:
        return -9
    return 0


def send_error(error):
    return JsonResponse({
        "error": error,
        "error_note": CLICK_ERRORS[error]
    })


# Prepare
@api_view(['POST'])
def click_prepare(request):
    sz = ClickPrepareSerializer(data=request.data)
    sz.is_valid(raise_exception=True)
    data = sz.validated_data
    err_code = data["error"]
    if err_code < 0:
        return send_error(-9)

    if check_signature(data) != data['sign_string']:
        return send_error(-1)
    action = data["action"]

    if action != 0:
        return send_error(-3)

    order_id: str = data["merchant_trans_id"]
    if not order_id.isnumeric() or len(order_id) > 18 or abs(int(order_id)) > 9223372036854775807:
        return send_error(-5)
    order: Order = Order.objects.filter(pk=order_id).first()
    error = get_error_code(order, data)
    if error:
        return send_error(error)
    try:
        click_pay: ClickPayment = ClickPayment.objects.create(
            order=order,
            transactionId=data["click_trans_id"],
            sign_time=timezone.datetime.strptime(data["sign_time"], "%Y-%m-%d %H:%M:%S"),
            action=action
        )
    except Exception:
        return send_error(-8)

    return JsonResponse({
        "error": error,
        "error_note": CLICK_ERRORS[error],
        "click_trans_id": data['click_trans_id'],
        "merchant_trans_id": data['merchant_trans_id'],
        "merchant_prepare_id": click_pay.id
    })


@api_view(['POST'])
def click_complete(request):
    serializer = ClickCompleteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if check_signature(data) != data['sign_string']:
        return send_error(-1)

    if data["action"] != 1:
        return send_error(-3)

    merchant_prepare_id = data["merchant_prepare_id"]
    click_pay: ClickPayment = ClickPayment.objects.filter(pk=merchant_prepare_id).first()

    if click_pay is None:
        return send_error(-6)

    order = click_pay.order
    error = get_error_code(order, data)
    if error:
        return send_error(error)

    order.status = Order.Status.PAID
    order.payment_app = Order.PaymentAppType.CLICK
    order.save()

    click_pay.action = 1
    click_pay.save()

    return JsonResponse({
        "error": error,
        "error_note": CLICK_ERRORS[error],
        "click_trans_id": data['click_trans_id'],
        "merchant_trans_id": data['merchant_trans_id'],
        "merchant_confirm_id": click_pay.id
    })

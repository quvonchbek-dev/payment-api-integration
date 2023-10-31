import base64
import datetime
import hashlib
import json
import os

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payment_api.enums import PaymeErrors
from payment_api.models import Order, Payment, ClickPayment, PayMeTransaction
from payment_api.serializers import CheckPaymentSerializerUzum, PaymentSerializer, ClickPrepareSerializer, \
    ClickCompleteSerializer
from payment_api.utils import successful_payment

load_dotenv('../.env')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
                        "amount": order.amount * 100
                    }
                }
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
        elif order.amount * 100 != amount:
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
            order.payment_app = Order.PaymentAppType.UZUM
            order.save()
            successful_payment(order)

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
        if order.status == Order.Status.PAID:
            return -4
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

    click_pay: ClickPayment = ClickPayment.objects.create(
        order=order,
        transactionId=data["click_trans_id"],
        sign_time=timezone.datetime.strptime(data["sign_time"], "%Y-%m-%d %H:%M:%S"),
        action=action
    )

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
    successful_payment(order)
    return JsonResponse({
        "error": error,
        "error_note": CLICK_ERRORS[error],
        "click_trans_id": data['click_trans_id'],
        "merchant_trans_id": data['merchant_trans_id'],
        "merchant_confirm_id": click_pay.id
    })


"""
PAYME INTEGRATION - https://developer.help.paycom.uz/metody-merchant-api/
"""


def check_order(order: Order):
    if order is None:
        return PaymeErrors.ORDER_NOT_FOUND
    if order.status == Order.Status.PAID:
        return PaymeErrors.ALREADY_PAID
    if order.status == Order.Status.EXPIRED:
        return PaymeErrors.ORDER_EXPIRED
    if order.status == Order.Status.CANCELLED:
        return PaymeErrors.ORDER_CANCELLED


def payme_check_perform(data: dict):
    params = data["params"]
    res = {"id": data.get("id")}
    order_id = params["account"].get("id")

    if order_id is None:
        res["error"] = PaymeErrors.JSON_RPC_ERROR
        return res

    order = Order.objects.filter(pk=order_id).first()
    amount = params.get("amount")
    error = check_order(order)
    if error:
        res["error"] = error
    elif order.amount * 100 != amount:
        res["error"] = PaymeErrors.WRONG_AMOUNT
    else:
        res["result"] = dict(allow=True)
    return res


def payme_create(data: dict):
    params = data["params"]
    res = {"id": data.get("id")}
    tr = PayMeTransaction.objects.filter(transaction_id=params["id"]).first()
    if tr is None:
        check = payme_check_perform(data)
        if check.get("result") is None or not check["result"]["allow"]:
            return check
        order = Order.objects.filter(pk=params["account"]["id"]).first()
        tr = PayMeTransaction.objects.create(
            transaction_id=params["id"],
            time=timezone.datetime.fromtimestamp(params['time'] / 1000),
            create_time=timezone.now(),
            order=order)
        successful_payment(order)
    else:
        order = tr.order
        delta = tr.create_time + datetime.timedelta(seconds=43_200)
        expired = delta < timezone.now()
        if expired and order.status == Order.Status.WAITING:
            order.status = Order.Status.EXPIRED
            order.save()
        if order.status == Order.Status.WAITING:
            res["error"] = PaymeErrors.CANT_PERFORM_TRANS
            return res

    res["result"] = dict(create_time=int(tr.create_time.timestamp()), transaction=str(tr.id), state=1)
    return res


def payme_perform(data: dict):
    tr_id = data["params"]["id"]
    tr: PayMeTransaction = PayMeTransaction.objects.filter(transaction_id=tr_id).first()
    res = {"id": data.get("id")}
    if tr is None:
        res["error"] = PaymeErrors.TRANS_NOT_FOUND
        return res

    order = tr.order
    if order.status == Order.Status.WAITING:
        if tr.create_time + datetime.timedelta(hours=12) < timezone.now():
            order.status = Order.Status.EXPIRED
            order.save()
            res["error"] = PaymeErrors.CANT_PERFORM_TRANS
            return res

        order.status = Order.Status.PAID
        order.save()
        tr.perform_time = timezone.now()
        tr.save()
        res["result"] = dict(transaction=str(tr.id), perform_time=int(tr.perform_time.timestamp()), state=2)
    else:
        if order.status == Order.Status.PAID:
            res["result"] = dict(transaction=str(tr.id), perform_time=int(tr.perform_time.timestamp()), state=2)
        else:
            res["error"] = PaymeErrors.CANT_PERFORM_TRANS
    return res


def payme_cancel(data: dict):
    tr: PayMeTransaction = PayMeTransaction.objects.filter(transaction_id=data["params"]["id"]).first()
    res = {"id": data.get("id")}
    if tr is None:
        res["error"] = PaymeErrors.TRANS_NOT_FOUND
        return res

    order = tr.order
    if order.status == Order.Status.WAITING:
        order.status = Order.Status.CANCELLED
        order.save()

        tr.cancel_time = timezone.now()
        tr.save()

        res["result"] = dict(state=-1, transaction=str(tr.id), cancel_time=int(tr.cancel_time.timestamp()))
    elif order.status == Order.Status.PAID:
        res["error"] = PaymeErrors.CANT_CANCEL_TRANSACTION
    else:
        order.status = Order.Status.CANCELLED
        order.save()
        tr.cancel_time = timezone.now()
        tr.save()
        res["result"] = dict(state=-2, transaction=str(tr.id), cancel_time=int(tr.cancel_time.timestamp()))
    return res


def payme_check_transaction(data: dict[dict]):
    tr: PayMeTransaction = PayMeTransaction.objects.filter(transaction_id=data["params"]["id"]).first()
    res = {"id": data.get("id")}

    if tr is None:
        res["error"] = PaymeErrors.TRANS_NOT_FOUND
    else:
        order = tr.order
        state = order.status + 1
        if order.status > Order.Status.PAID:
            state = -1 - (order.status == Order.Status.EXPIRED)
        res["result"] = dict(
            create_time=tr.create_time.timestamp() * 1000,
            perform_time=tr.perform_time.timestamp() * 1000 if order.status == Order.Status.PAID else 0,
            cancel_time=tr.perform_time.timestamp() * 1000 if order.status == Order.Status.CANCELLED else 0,
            transaction=str(tr.id),
            state=state
        )
    return res


def payme_get_statement(data: dict[dict]):
    params = data["params"]
    start = datetime.datetime.fromtimestamp(params["from"])
    end = datetime.datetime.fromtimestamp(params["to"])
    qs: QuerySet[PayMeTransaction] = PayMeTransaction.objects.filter(
        create_time__gte=start).filter(
        create_time__lte=end).order_by("create_time")
    transactions = []
    for tr in qs:
        order = tr.order
        state = order.status + 1
        if order.status > Order.Status.PAID:
            state = -1 - (order.status == Order.Status.EXPIRED)
        transactions.append(dict(
            id=tr.transaction_id,
            time=tr.time,
            amount=order.amount * 100,
            account=dict(id=tr.order.id),
            create_time=int(tr.create_time.timestamp()),
            perform_time=int(tr.perform_time.timestamp()) if order.status == Order.Status.PAID else 0,
            cancel_time=int(tr.cancel_time.timestamp()) if order.status == Order.Status.CANCELLED else 0,
            transaction=str(tr.id),
            state=state
        ))
    return dict(result=dict(transactions=transactions))


def check_request(request: WSGIRequest):
    if request.method != "POST":
        return PaymeErrors.INVALID_HTTP_METHOD

    auth_token = request.headers.get("Authorization")
    if auth_token is None:
        return PaymeErrors.AUTH_ERROR

    auth = base64.b64decode(auth_token.split()[1]).decode("utf-8")
    if auth != os.getenv('PAYME_TEST_LOGIN') + ":" + os.getenv('PAYME_TEST_KEY'):
        return PaymeErrors.AUTH_ERROR

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.decoder.JSONDecodeError:
        return dict(error=PaymeErrors.PARSING_JSON)

    if not ("method" in data or "params" in data):
        return PaymeErrors.JSON_RPC_ERROR

    return False


@csrf_exempt
def payme_all(request: WSGIRequest):
    error = check_request(request)
    if error:
        return JsonResponse(dict(error=error))

    data = json.loads(request.body.decode("utf-8"))
    method = data["method"]

    if method == "CreateTransaction":
        return JsonResponse(payme_create(data))
    elif method == "PerformTransaction":
        return JsonResponse(payme_perform(data))
    elif method == "CheckPerformTransaction":
        return JsonResponse(payme_check_perform(data))
    elif method == "CancelTransaction":
        return JsonResponse(payme_cancel(data))
    elif method == "CheckTransaction":
        return JsonResponse(payme_check_transaction(data))
    elif method == "GetStatement":
        return JsonResponse(payme_get_statement(data))

    return JsonResponse(dict(error=PaymeErrors.METHOD_NOT_FOUND, id=data["id"]))

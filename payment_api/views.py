import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import hashlib
from .models import Payment, ClickTransaction
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


from django.http import JsonResponse
import hashlib
from .models import ClickTransaction

SECRET_KEY = "YOUR_SECRET_KEY"  # Replace with your actual secret key


def check_signature(data):
    if data['action'] == 0:  # Prepare
        sign_string = f"{data['click_trans_id']}{data['service_id']}{SECRET_KEY}{data['merchant_trans_id']}{data['amount']}{data['action']}{data['sign_time']}"
    elif data['action'] == 1:  # Complete
        sign_string = f"{data['click_trans_id']}{data['service_id']}{SECRET_KEY}{data['merchant_trans_id']}{data['merchant_prepare_id']}{data['amount']}{data['action']}{data['sign_time']}"
    else:
        return
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest()


@require_POST
def prepare(request):
    data = request.POST

    # Check Signature
    if check_signature(data) != data['sign_string']:
        return JsonResponse({
            "error": -1,
            "error_note": "SIGN CHECK FAILED!"
        })

    order = Order.objects.get()
    # Logic to verify the payment here. You might need to interact with your main system or database to check the payment details.
    # For now, I'll assume that the payment verification is always successful.

    # Assuming everything went well, return a success response
    return JsonResponse({
        "error": 0,
        "error_note": "Success",
        "click_trans_id": data['click_trans_id'],
        "merchant_trans_id": data['merchant_trans_id'],
        "merchant_prepare_id": 12345  # Replace with an actual ID from your system
    })


@require_POST
def complete(request):
    data = request.POST

    # Check Signature
    if check_signature(data) != data['sign_string']:
        return JsonResponse({
            "error": -1,
            "error_note": "SIGN CHECK FAILED!"
        })

    # Logic to complete the payment here. Again, you might need to interact with your main system or database.

    # Assuming everything went well, return a success response
    return JsonResponse({
        "error": 0,
        "error_note": "Success",
        "click_trans_id": data['click_trans_id'],
        "merchant_trans_id": data['merchant_trans_id'],
        "merchant_confirm_id": 67890  # Replace with an actual ID from your system
    })

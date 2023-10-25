from django.utils import timezone

from payment_api.models import Order


def successful_payment(order: Order):
    user = order.owner
    tariff = order.tariff
    delta = timezone.timedelta(days=int(tariff.month))
    if tariff.turi == "avtorassilka":
        user.podpiski1_end += delta
    elif tariff.turi == "poiskgruzov":
        user.podpiski2_end += delta
    else:
        user.podpiski1_end += delta
        user.podpiski2_end += delta
    user.save()
    print("SUCCESSFUL PAYMENT ORDER", order.id, "APP:", order.payment_app, "AMOUNT:", order.amount)

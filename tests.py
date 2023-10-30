import random
import time
import unittest

import requests
from django.db.models import QuerySet
from django.utils import timezone
from core import wsgi

from payment_api.models import Order, User, PayMeTransaction, Tarif

a = wsgi.application


class TestPayme(unittest.TestCase):
    url = "http://localhost:8000/api/payment/payme/"
    auth = ("admin", "admin")
    amount = 5000
    order: Order = Order.objects.create(
        owner=User.users.first(),
        amount=amount,
        tariff=Tarif.objects.first(),
        payment_for=random.randint(0, 2),
        payment_app="payme"
    )
    session = requests.session()
    session.auth = auth

    def test_1_check_perform_transaction(self):
        order = self.order
        data = dict(method="CheckPerformTransaction", params=dict(amount=self.amount * 100,
                                                                  account=dict(id=order.id)), id=123)
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["result"]["allow"], True, "Allow should be True")

        data["params"]["account"]["id"] *= 10
        res = self.session.post(self.url, json=data).json()
        data["params"]["account"]["id"] //= 10
        self.assertEqual(res["error"]["code"], -31050, "Order should not be found")

        order.status = Order.Status.PAID
        order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["error"]["code"], -31051, "Order status is PAID")

        order.status = Order.Status.CANCELLED
        order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["error"]["code"], -31053, "Order status is CANCELLED")

        order.status = Order.Status.WAITING
        order.save()

        data["params"]["amount"] += 1
        res = self.session.post(self.url, json=data).json()
        data["params"]["amount"] -= 1
        self.assertEqual(res["error"]["code"], -31001, "Amount should different")

    def test_2_create_transaction(self):
        now = timezone.now()
        data = dict(
            method="CreateTransaction",
            params=dict(id=f"test_{int(time.time())}", time=now.timestamp(),
                        amount=self.amount * 100, account=dict(id=self.order.id)), id=123)
        res = self.session.post(self.url, json=data).json()
        self.assertIn("result", res, "Result")

        tr: PayMeTransaction = PayMeTransaction.objects.filter(pk=res["result"]["transaction"]).first()
        tr.create_time -= timezone.timedelta(days=0.5)
        tr.save()
        data["params"]["time"] = (now - timezone.timedelta(days=0.5)).timestamp()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["error"]["code"], -31008, "Should be expired")

        tr.create_time += timezone.timedelta(days=0.5)
        tr.save()
        data["params"]["time"] = now.timestamp()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["error"]["code"], -31008, "Should be Cancelled/Expired")

    def test_3_perform_transaction(self):
        tr: PayMeTransaction = self.order.payme_transactions.first()
        data = dict(method="PerformTransaction", params=dict(id=tr.transaction_id))
        res = self.session.post(self.url, json=data).json()
        self.assertIn("error", res, "Transaction should be cancelled")

        self.order.status = Order.Status.WAITING
        self.order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertIn("result", res, "Status should be PAID")

    def test_4_cancel_transaction(self):
        tr: PayMeTransaction = self.order.payme_transactions.first()
        data = dict(method="CancelTransaction", params=dict(id=tr.transaction_id))
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["error"]["code"], -31007)

        self.order.status = Order.Status.EXPIRED
        self.order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["result"]["state"], -2)

        self.order.status = Order.Status.WAITING
        self.order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["result"]["state"], -1)

    def test_5_check_transaction(self):
        tr: PayMeTransaction = self.order.payme_transactions.first()
        data = dict(method="CheckTransaction", params=dict(id=tr.transaction_id))
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["result"]["state"], -1)

        self.order.status = Order.Status.EXPIRED
        self.order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["result"]["state"], -2)

        self.order.status = Order.Status.WAITING
        self.order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["result"]["state"], 1)

        self.order.status = Order.Status.PAID
        self.order.save()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["result"]["state"], 2)

    def test_6_get_statement(self):
        end = timezone.now()
        start = end - timezone.timedelta(hours=1)
        data = {
            "method": "GetStatement",
            "params": {
                "from": int(start.timestamp()),
                "to": int(end.timestamp())
            }
        }
        res = self.session.post(self.url, json=data).json()
        qs: QuerySet[PayMeTransaction] = PayMeTransaction.objects.filter(
            create_time__gte=start).filter(
            create_time__lte=end).order_by("create_time")

        self.assertEqual(qs.count(), len(res["result"]["transactions"]), )


if __name__ == '__main__':
    unittest.main()

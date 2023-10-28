import datetime
import random
import time
import unittest

import requests

from core import wsgi
from payment_api.models import Order, User, PayMeTransaction

a = wsgi.application


class TestPayme(unittest.TestCase):
    url = "http://localhost:8000/api/payment/payme/"
    auth = ("admin", "admin")
    amount = 5000
    order: Order = Order.objects.create(
        owner=User.users.first(),
        amount=amount,
        payment_for=random.randint(0, 2),
        payment_app="payme"
    )
    session = requests.session()
    session.auth = auth

    def test_check_perform_transaction(self):
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
        self.order.refresh_from_db()

    def test_create_transaction(self):
        now = datetime.datetime.now()
        data = dict(
            method="CreateTransaction",
            params=dict(id=f"test_{int(time.time())}", time=now.timestamp(),
                        amount=self.amount * 100, account=dict(id=self.order.id)), id=123)
        res = self.session.post(self.url, json=data).json()
        self.assertIn("result", res, "Result")

        tr: PayMeTransaction = PayMeTransaction.objects.filter(pk=res["result"]["transaction"]).first()
        tr.create_time -= datetime.timedelta(days=0.5)
        tr.save()
        data["params"]["time"] = (now - datetime.timedelta(days=0.5)).timestamp()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["error"]["code"], -31008, "Should be expired")

        tr.create_time += datetime.timedelta(days=0.5)
        tr.save()
        data["params"]["time"] = now.timestamp()
        res = self.session.post(self.url, json=data).json()
        self.assertEqual(res["error"]["code"], -31008, "Should be Cancelled/Expired")




if __name__ == '__main__':
    unittest.main()

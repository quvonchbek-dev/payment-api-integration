from django.contrib import admin

from .models import User, Payment, Order, ClickPayment

admin.site.register([Payment, User, Order, ClickPayment])
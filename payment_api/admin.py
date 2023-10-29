from django.contrib import admin

from .models import Order, Payment, ClickPayment, PayMeTransaction, Tarif, User


class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "status", "amount", "payment_for", "payment_app", "created_at"]
    list_filter = ["status", "payment_for", "owner", "amount", "payment_app"]


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "order", "status", "transactionId"]
    list_filter = []

    def status(self, obj: Payment):
        return ["WAITING", "PAID", "CANCELLED", "EXPIRED"][obj.order.status]

    def name(self, obj: Payment):
        return f"{obj.order.owner.name}"


class ClickPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "order", "status", "action", "sign_time"]
    list_filter = ["action"]

    def name(self, obj: ClickPayment):
        return f"{obj.order.owner.name}"


class PayMeTransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "time", "create_time"]


admin.site.register(Order, OrderAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(ClickPayment, ClickPaymentAdmin)
admin.site.register(PayMeTransaction, PayMeTransactionAdmin)
admin.site.register(Tarif)
admin.site.register(User)


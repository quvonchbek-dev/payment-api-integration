from django.db import models


class User(models.Model):
    users = models.Manager()
    name = models.CharField(verbose_name="Полное имя", null=True, blank=True, max_length=200)
    username = models.CharField(verbose_name="Имя пользователя", null=True, blank=True, max_length=200)
    telegram_id = models.BigIntegerField(verbose_name="Идентификатор телеграммы", unique=True)
    tel_number = models.CharField(verbose_name="Номер телефона", max_length=20, null=True, blank=True)
    status = models.CharField(verbose_name="Позиция",
                              choices=(
                                  ('maxsus', '✅ Спец. пользователь'), ("new_maxsus", '✅ Восст. Спец. пользователь'),
                                  ('student', '👨‍🏫 Студент'), ('new_student', '👨‍🏫 Восст. Студент'),
                                  ('graduate', '👨‍🎓 Старые студенты'),
                                  ('new_graduate', '👨‍🎓 Восст. Старые студенты')),
                              max_length=100,
                              null=True, blank=True)
    kod = models.CharField(verbose_name="Код доступа к боту", max_length=15, null=True, blank=True)
    my_kod = models.CharField(verbose_name="Код восстановления", max_length=15, null=True, blank=True)
    isadmin = models.BooleanField(verbose_name='Админ', default=False)
    lang = models.CharField(verbose_name="Язык бота", choices=(('uz', 'узбекский'), ('ru', 'Русский')), default='uz',
                            max_length=100, null=True, blank=True)
    start_data = models.DateTimeField(verbose_name="Дата регистрации", auto_now_add=True, null=True, blank=True)
    balans1_avto = models.FloatField(verbose_name="АвтоРассылки баланса", default=0, null=True, blank=True)
    balans2_yuk = models.FloatField(verbose_name="Баланс поиска груза", default=0, null=True, blank=True)
    balans_ikkalasi = models.FloatField(verbose_name="Баланс АвтоРассылки и Поиски груза", default=0, null=True,
                                        blank=True)
    valyuta = models.CharField(verbose_name="Валюта", max_length=100, default='UZS', null=True, blank=True)
    podpiski1 = models.DateTimeField(verbose_name="\"Автоотправку\" времени подписки", null=True, blank=True)
    podpiski1_end = models.DateTimeField(verbose_name="\"Автоотправку\" даты окончания подписки", null=True, blank=True)
    podpiski2 = models.DateTimeField(verbose_name="\"Поиск груза\" времени подписки", null=True, blank=True)
    podpiski2_end = models.DateTimeField(verbose_name="\"Поиск груза\" даты окончания подписки", null=True, blank=True)
    tolov_avto_yuk = models.CharField(verbose_name="Последний оплаченный раздел", max_length=100, null=True, blank=True,
                                      editable=False)
    oxirgi_price = models.FloatField(verbose_name="Сумма последнего платежа", default=0, null=True, blank=True,
                                     editable=False)
    send_group_link = models.CharField(verbose_name='Ссылка на группу отправлена', max_length=100, null=True,
                                       blank=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Пользователь бота"
        verbose_name_plural = "Пользователи бота"


class Tarif(models.Model):
    turi = models.CharField(verbose_name="Тип возможности",
                            choices=(('avtorassilka', 'АвтоРассылки'),
                                     ('poiskgruzov', 'Поиски грузов'),
                                     ('ikkalasi', 'Оба из них')),
                            max_length=30,
                            null=True, blank=True)
    month = models.CharField(verbose_name="Количество дней",
                             choices=(('3', '3 день'), ('5', '5 день'),
                                      ('7', '7 день'), ('15', '15 день'),
                                      ('30', '1 месяц'), ('60', '2 месяц'),
                                      ('90', '3 месяц'), ('120', '4 месяц'),
                                      ('150', '5 месяц'), ('180', '6 месяц'),
                                      ('210', '7 месяц'), ('240', '8 месяц'),
                                      ('270', '9 месяц'), ('300', '10 месяц'),
                                      ('330', '11 месяц'), ('360', '1 год'),
                                      ('720', '2 год')),
                             max_length=30, null=True, blank=True)
    price = models.IntegerField(verbose_name='Цена (в сумах)', default=0, null=True, blank=True)
    chegirma = models.CharField(verbose_name="Скидка", max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"

    def __str__(self):
        return f"{self.month}"


class Order(models.Model):
    class Status(models.IntegerChoices):
        WAITING = 0
        PAID = 1
        CANCELLED = 2
        EXPIRED = 3

    class OrderTypes(models.IntegerChoices):
        AUTOSEND = 0
        SEARCH = 1
        ALL = 2

    class PaymentAppType(models.TextChoices):
        NONE = "none"
        UZUM = "uzum"
        CLICK = "click"
        PAYME = "payme"

    owner = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices, default=Status.WAITING)
    amount = models.BigIntegerField()
    payment_for = models.IntegerField(choices=OrderTypes.choices, default=OrderTypes.ALL)
    tariff = models.ForeignKey(Tarif, on_delete=models.SET_NULL, related_name="tariff_payments", blank=True,
                               null=True, default=None)
    created_at = models.DateTimeField(editable=True, auto_now_add=True, null=True)
    payment_app = models.CharField(max_length=10, choices=PaymentAppType.choices, default=PaymentAppType.NONE)

    def __str__(self):
        return f"{self.id}. {self.owner.name} - {self.amount} so'm"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Payment(models.Model):
    order = models.ForeignKey(Order, models.CASCADE, 'payments')
    transactionId = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Uzum"
        verbose_name_plural = "Uzum"

    def __str__(self):
        return f"{self.order.owner.name} - {self.order.amount} sum"


class ClickPayment(models.Model):
    class ActionTypes(models.IntegerChoices):
        PREPARING = 0
        COMPLETE = 1

    order = models.ForeignKey(Order, models.CASCADE, 'click_payment')
    transactionId = models.BigIntegerField()
    action = models.IntegerField(choices=ActionTypes.choices, default=0)
    sign_time = models.DateTimeField()

    @property
    def status(self):
        return ["Waiting", "Paid", "Cancelled", "Expired"][self.order.status]

    def __str__(self):
        return f"{self.order.id} | {self.order.owner.name} | {self.order.amount}"

    class Meta:
        verbose_name = "Click"
        verbose_name_plural = "Click"


class PayMeTransaction(models.Model):
    transaction_id = models.CharField(max_length=100)
    order = models.ForeignKey(Order, models.CASCADE, related_name='payme_transactions')
    time = models.DateTimeField()
    create_time = models.DateTimeField(auto_now_add=True)
    perform_time = models.DateTimeField(null=True, blank=True)
    cancel_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "PayMe"
        verbose_name_plural = "PayMe"

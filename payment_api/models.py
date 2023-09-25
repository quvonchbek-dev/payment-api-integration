from django.db import models



class User(models.Model):
    users = models.Manager()
    name = models.CharField(verbose_name="Полное имя", null=True, blank=True, max_length=100)
    username = models.CharField(verbose_name="Имя пользователя", null=True, blank=True, max_length=200, unique=True)
    telegram_id = models.BigIntegerField(verbose_name="Идентификатор телеграммы", unique=True)
    tel_number = models.CharField(verbose_name="Номер телефона", max_length=20, null=True, blank=True)
    status = models.CharField(verbose_name="Позиция",
                              choices=(
                                  ('maxsus', '✅ Спец. пользователь'), ("new_maxsus", '✅ Восст. Спец. пользователь'),
                                  ('student', '👨‍🏫 Студент'), ('new_student', '👨‍🏫 Восст. Студент'),
                                  ('graduate', '👨‍🎓 Старые студенты'),
                                  ('new_graduate', '👨‍🎓 Восст. Старые студенты')),
                              max_length=30,
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

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Пользователь бота"
        verbose_name_plural = "Пользователи бота"


class Order(models.Model):
    class Status(models.IntegerChoices):
        WAITING = 0
        USED = 1
        CANCELLED = 2
        EXPIRED = 3

    class OrderTypes(models.IntegerChoices):
        AUTOSEND = 0
        SEARCH = 1
        ALL = 2

    owner = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE)
    # error = models.CharField(max_length=30, choices=Error.choices, blank=True)
    status = models.IntegerField(choices=Status.choices, default=Status.WAITING)
    amount = models.BigIntegerField()
    payment_for = models.IntegerField(choices=OrderTypes.choices, default=OrderTypes.ALL)
    created_at = models.DateTimeField(editable=True, auto_now_add=True)

    def __str__(self):
        return f"{str(self.id)} - {self.owner.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Payment(models.Model):
    order = models.ForeignKey(Order, models.CASCADE, 'payments')
    transactionId = models.CharField(max_length=255)


class ClickTransaction(models.Model):
    click_trans_id = models.BigIntegerField(unique=True)
    service_id = models.IntegerField()
    click_paydoc_id = models.BigIntegerField()
    merchant_trans_id = models.CharField(max_length=255)
    amount = models.FloatField()
    action = models.IntegerField()
    error = models.IntegerField()
    error_note = models.CharField(max_length=255)
    sign_time = models.DateTimeField()
    sign_string = models.CharField(max_length=255)
    merchant_prepare_id = models.IntegerField(null=True, blank=True)
    merchant_confirm_id = models.IntegerField(null=True, blank=True)



    def __str__(self):
        return str(self.click_trans_id)

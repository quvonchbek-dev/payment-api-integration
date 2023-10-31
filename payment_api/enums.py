class Error:
    def __init__(self, code, uz, ru, en):
        self.uz = uz
        self.ru = ru
        self.en = en
        self.code = code

    @property
    def json(self):
        return dict(code=self.code, message=dict(ru=self.ru, uz=self.uz, en=self.en))


class PaymeErrors:
    TRANS_ALREADY_EXISTS = Error(-31054, "Tranzaksiya allaqachon yaratilgan", "Транзакция уже существует",
                                 "Transaction already exists").json
    ORDER_EXPIRED = Error(-31052, ru="Срок действия заказа истек", uz="Buyurtma muddati tugagan",
                          en="Order expired").json
    ORDER_CANCELLED = Error(-31053, ru="Заказ отменен", uz="Buyurtma bekor qilindi", en="Order cancelled").json
    ALREADY_PAID = Error(-31051, ru="Уже оплачено", uz="Allaqachon to'langan", en="Already paid").json
    INVALID_HTTP_METHOD = Error(-32300, "So'rov POST bo'lishi kerak", "Запрос должен быть POST",
                                "Request should be POST").json
    PARSING_JSON = Error(-32700, "JSON bilan bog'liq xato.", "Ошибка парсинга JSON.", "JSON parsing error").json
    SYSTEM_ERROR = Error(-32400, "Ichki sistema xatoligi", "Внутренняя ошибка сервера", "Internal server error").json
    AUTH_ERROR = Error(-32504, "Avtorizatsiyadan o'tishda xatolik", "Ошибка аутентификации", "Auth error").json
    WRONG_AMOUNT = Error(-31001, "Noto'g'ri summa.", "Неверная сумма.", "Wrong amount.", ).json
    ORDER_NOT_FOUND = Error(-31050, ru="Заказ не найден", uz="Buyurtma topilmadi", en="Order not found").json
    JSON_RPC_ERROR = Error(-32600, "Notog`ri JSON-RPC obyekt yuborilgan.", "Передан неправильный JSON-RPC объект.",
                           "Handed the wrong JSON-RPC object.").json
    TRANS_NOT_FOUND = Error(-31003, "Transaction not found", "Трансакция не найдена", "Transaksiya topilmadi").json
    METHOD_NOT_FOUND = Error(-32601, "Metod topilmadi", "Запрашиваемый метод не найден.", "Method not found").json
    CANT_PERFORM_TRANS = Error(-31008, "Bu operatsiyani bajarish mumkin emas", "Невозможно выполнить данную операцию.",
                               "Can't perform transaction", ).json
    CANT_CANCEL_TRANSACTION = Error(-31007, "Transaksiyani qayyarib bolmaydi", "Невозможно отменить транзакцию",
                                    "You can not cancel the transaction").json
    PENDING_PAYMENT = Error(-31099, "To'lov kutilmoqda", "В ожидании оплаты", "Pending payment").json

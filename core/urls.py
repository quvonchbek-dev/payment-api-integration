from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from payment_api.views import check_payment, process_payment, click_prepare, click_complete

urlpatterns = ([
                   path('admin/', admin.site.urls, name='admin'),
                   path('api/payment/uzum/check', check_payment),
                   path('api/payment/uzum/pay', process_payment),
                   path('api/payment/click/prepare', click_prepare),
                   path('api/payment/click/complete', click_complete),
               ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))

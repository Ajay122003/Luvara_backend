# from django.urls import path
# from .views import *

# urlpatterns = [
#     path("create/", CreateRazorpayOrderAPIView.as_view()),
#     path("verify/", VerifyRazorpayPaymentAPIView.as_view()),
#     path("webhook/", RazorpayWebhookAPIView.as_view()),

# ]

from django.urls import path
from .views import *

urlpatterns = [
    path("create/", CreateCashfreeOrderAPIView.as_view()),
    path("verify/", VerifyCashfreePaymentAPIView.as_view()),
    path("webhook/", CashfreeWebhookAPIView.as_view()),
]

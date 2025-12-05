from django.urls import path
from .views import *

urlpatterns = [
    path("create/", CreateRazorpayOrderAPIView.as_view()),
    path("verify/", VerifyPaymentAPIView.as_view()),
]

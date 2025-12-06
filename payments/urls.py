from django.urls import path
from .views import CreateRazorpayOrderAPIView, VerifyRazorpayPaymentAPIView

urlpatterns = [
    path("create/", CreateRazorpayOrderAPIView.as_view()),
    path("verify/", VerifyRazorpayPaymentAPIView.as_view()),
]

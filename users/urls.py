from django.urls import path
from .views import *

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-otp/", VerifyOTPAPIView.as_view()),
    path("login/", LoginView.as_view()),
    path("me/", MeView.as_view()),
]

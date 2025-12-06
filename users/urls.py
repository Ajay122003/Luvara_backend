from django.urls import path
from .views import *

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/send-otp/", LoginSendOTPView.as_view()),
    path("login/verify-otp/", LoginVerifyOTPView.as_view()),
    path("login/", LoginView.as_view()),   # if you keep password login
    path("me/", MeView.as_view()),
    path("logout/", LogoutView.as_view()),
]

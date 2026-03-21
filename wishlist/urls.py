from django.urls import path
from .views import *

urlpatterns = [
    path("", WishlistListAPIView.as_view()),          # GET
    path("toggle/", WishlistToggleAPIView.as_view()), # POST
    path("status/", WishlistStatusAPIView.as_view()), # GET
]

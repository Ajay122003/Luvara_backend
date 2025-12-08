from django.urls import path
from .views import *

urlpatterns = [
    path("", WishlistListAPIView.as_view()),
    path("toggle/", WishlistToggleAPIView.as_view()),
    path("<int:item_id>/remove/", WishlistRemoveAPIView.as_view()),
    path("status/", WishlistStatusAPIView.as_view()),   # NEW
]

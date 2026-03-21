from django.urls import path
from .views import *

urlpatterns = [
    path("add/", AddToCartAPIView.as_view()),
    path("", CartListAPIView.as_view()),
    path("<int:item_id>/update/", UpdateCartItemAPIView.as_view()),
    path("<int:item_id>/remove/", RemoveCartItemAPIView.as_view()),
]

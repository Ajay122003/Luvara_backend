from django.urls import path
from .views import *

urlpatterns = [
    path("create/", OrderCreateAPIView.as_view()),
    path("", UserOrderListAPIView.as_view()),                # /api/orders/
    path("<int:order_id>/", UserOrderDetailAPIView.as_view()) 
]

from django.urls import path
from .views import *

urlpatterns = [
    path("create/", OrderCreateAPIView.as_view()),
    path("", UserOrderListAPIView.as_view()),                     # GET /api/orders/
    path("<int:order_id>/", UserOrderDetailAPIView.as_view()),    # GET /api/orders/1/
    path("<int:order_id>/cancel/", CancelOrderAPIView.as_view()),
    path("<int:order_id>/return/", RequestReturnAPIView.as_view()),
    path("<int:order_id>/invoice/", OrderInvoiceAPIView.as_view()),
]

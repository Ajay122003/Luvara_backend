from django.urls import path
from .views import OfferListAPIView, OfferDetailAPIView

urlpatterns = [
    path("", OfferListAPIView.as_view()),               # /api/offers/
    path("<slug:slug>/", OfferDetailAPIView.as_view()), # /api/offers/diwali-sale/
]

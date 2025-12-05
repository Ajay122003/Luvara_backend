from django.urls import path
from .views import AddressListCreateAPIView, AddressDetailAPIView

urlpatterns = [
    path("", AddressListCreateAPIView.as_view()),      # /api/address/
    path("<int:pk>/", AddressDetailAPIView.as_view()), # /api/address/1/
]


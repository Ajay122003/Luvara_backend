from django.urls import path
from .views import *

urlpatterns = [
    path("", AddressListCreateAPIView.as_view()),      # /api/address/
    path("<int:pk>/", AddressDetailAPIView.as_view()), # /api/address/1/
    path("<int:pk>/set-default/", SetDefaultAddressAPIView.as_view()),

]


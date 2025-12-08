from django.urls import path
from .views import *

urlpatterns = [
   # PUBLIC
    path("", PublicProductListAPIView.as_view()),
    path("<int:pk>/", PublicProductDetailAPIView.as_view()),
]

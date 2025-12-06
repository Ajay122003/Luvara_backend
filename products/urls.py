from django.urls import path
from .views import *

urlpatterns = [
    path("", ProductListCreateAPIView.as_view()),
    path("<int:pk>/", ProductDetailAPIView.as_view()),
    path("delete-image/<int:image_id>/", DeleteProductImageAPIView.as_view()),
]

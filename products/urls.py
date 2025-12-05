from django.urls import path
from .views import *

urlpatterns = [
    path("", ProductListCreateAPIView.as_view()),     # /api/products/
    path("<int:pk>/", ProductDetailAPIView.as_view()), # /api/products/1/
     path("delete-image/<int:image_id>/", DeleteProductImageAPIView.as_view())
]

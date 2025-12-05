from django.urls import path
from .views import *

urlpatterns = [
    path("", CategoryListCreateAPIView.as_view()),        # /api/categories/
    path("<int:pk>/", CategoryDetailAPIView.as_view()),   # /api/categories/1/
]

from django.urls import path
from .views import *

urlpatterns = [
    path("", CategoryListAPIView.as_view()),        # /api/categories/
    path("<int:pk>/", CategoryDetailAPIView.as_view()),   # /api/categories/1/
    path("<slug:slug>/", CategoryDetailAPIView.as_view()), 
]

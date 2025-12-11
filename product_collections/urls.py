from django.urls import path
from .views import CollectionListAPIView, CollectionDetailAPIView

urlpatterns = [
    path("", CollectionListAPIView.as_view()),                # GET /api/collections/
    path("<slug:slug>/", CollectionDetailAPIView.as_view()),  # GET /api/collections/<slug>/
]

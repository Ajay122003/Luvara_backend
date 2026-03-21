from django.urls import path
from .views import CollectionListAPIView, CollectionDetailAPIView

urlpatterns = [
    path("", CollectionListAPIView.as_view()),                    # /api/collections/
    path("slug/<slug:slug>/", CollectionDetailAPIView.as_view()), # /api/collections/slug/men/
]

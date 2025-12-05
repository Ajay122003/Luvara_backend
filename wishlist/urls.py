from django.urls import path
from .views import WishlistListAPIView, WishlistToggleAPIView, WishlistRemoveAPIView

urlpatterns = [
    path("", WishlistListAPIView.as_view()),               # GET /api/wishlist/
    path("toggle/", WishlistToggleAPIView.as_view()),      # POST /api/wishlist/toggle/
    path("<int:item_id>/remove/", WishlistRemoveAPIView.as_view()),  # DELETE /api/wishlist/3/remove/
]

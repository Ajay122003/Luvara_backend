from django.urls import path
from .views import *

urlpatterns = [
    path("login/", AdminLoginAPIView.as_view()),
    path("test/", AdminTestAPIView.as_view()),  # Only admin access
     # CATEGORY CRUD
    path("categories/", AdminCategoryListCreateAPIView.as_view()),
    path("categories/<int:pk>/", AdminCategoryDetailAPIView.as_view()),

    # PRODUCT CRUD
    path("products/", AdminProductListCreateAPIView.as_view()),
    path("products/<int:pk>/", AdminProductDetailAPIView.as_view()),
    
    # ORDER
    path("orders/", AdminOrderListAPIView.as_view()),          # GET all orders
    path("orders/<int:pk>/", AdminOrderDetailAPIView.as_view()),  # GET/PUT order detail

    # SETTINGS
    path("settings/", AdminSiteSettingsAPIView.as_view()),


]

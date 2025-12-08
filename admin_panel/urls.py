from django.urls import path
from .views import *

urlpatterns = [
    path("login/", AdminLoginAPIView.as_view()),
    path("verify-otp/", AdminVerifyOTPAPIView.as_view()), 
    path("test/", AdminTestAPIView.as_view()),
    path("update-email/", AdminUpdateEmailAPIView.as_view()),
    path("change-password/", AdminChangePasswordAPIView.as_view()),
    


    # CATEGORY CRUD
    path("categories/", AdminCategoryListCreateAPIView.as_view()),
    path("categories/<int:pk>/", AdminCategoryDetailAPIView.as_view()),

    # PRODUCT CRUD
    path("products/", AdminProductListCreateAPIView.as_view()),
    path("products/<int:pk>/", AdminProductDetailAPIView.as_view()),
    path("admin/delete-image/<int:image_id>/", AdminDeleteProductImageAPIView.as_view()),

    # ORDERS
    path("orders/", AdminOrderListAPIView.as_view()),
    path("orders/<int:pk>/", AdminOrderDetailAPIView.as_view()),

    # SETTINGS
    path("settings/", AdminSiteSettingsAPIView.as_view()),

    # DASHBOARD
    path("dashboard/", AdminDashboardStatsAPIView.as_view()),

    # LOW STOCK
    path("low-stock-products/", AdminLowStockProductsAPIView.as_view()),

    # COUPON ADMIN
    path("coupons/", AdminCouponListCreateAPIView.as_view()),
    path("coupons/<int:pk>/", AdminCouponDetailAPIView.as_view()),

]


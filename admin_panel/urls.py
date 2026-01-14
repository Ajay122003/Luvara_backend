from django.urls import path
from .views import *

urlpatterns = [
    # Auth
    path("login/", AdminLoginAPIView.as_view()),
    path("verify-otp/", AdminVerifyOTPAPIView.as_view()),
    path("test/", AdminTestAPIView.as_view()),
    path("users/", AdminUserListView.as_view()),
    path("subscriptions/", AdminSubscriptionListView.as_view()),
    path("forgot-password/", AdminForgotPasswordAPIView.as_view()),
    path("reset-password/", AdminResetPasswordAPIView.as_view()),
    



    # Profile
    path("update-email/", AdminUpdateEmailAPIView.as_view()),
    path("change-password/", AdminChangePasswordAPIView.as_view()),

    # Category
    path("categories/", AdminCategoryListCreateAPIView.as_view()),
    path("categories/<int:pk>/", AdminCategoryDetailAPIView.as_view()),

    # Collections
    path("collections/", AdminCollectionListCreateAPIView.as_view()),
    path("collections/<int:pk>/", AdminCollectionDetailAPIView.as_view()),


    # Product
    path("products/", AdminProductListCreateAPIView.as_view()),
    path("products/<int:pk>/", AdminProductDetailAPIView.as_view()),
    path("products/images/<int:image_id>/delete/", AdminDeleteProductImageAPIView.as_view()),

    # Orders
    path("orders/", AdminOrderListAPIView.as_view()),
    path("orders/<int:pk>/delete/", AdminOrderDeleteAPIView.as_view(),),
    path("orders/<int:pk>/", AdminOrderDetailAPIView.as_view()),

    # Settings
    path("settings/", AdminSiteSettingsAPIView.as_view()),
    path("public-settings/", PublicSiteSettingsAPIView.as_view()),


    # Dashboard
    path("dashboard/", AdminDashboardStatsAPIView.as_view()),
    path("low-stock-products/", AdminLowStockProductsAPIView.as_view()),

    # Coupons
    path("coupons/", AdminCouponListCreateAPIView.as_view()),
    path("coupons/<int:pk>/", AdminCouponDetailAPIView.as_view()),

    #offers
    path("offers/", AdminOfferListCreateAPIView.as_view()),
    path("offers/<int:pk>/", AdminOfferDetailAPIView.as_view()),

]

from django.urls import path

from . import views


urlpatterns = [
    path("", views.landing, name="landing"),
    path("buyer/", views.buyauth, name="buyer_auth"),
    path("seller/", views.sellerauth, name="seller_auth"),
    path("buyer/dashboard/", views.buyerdashboard, name="buyer_dashboard"),
    path("seller/dashboard/", views.sellerdashboard, name="seller_dashboard"),
    path("seller/listings/<int:listing_id>/edit/", views.seller_listing_edit, name="seller_listing_edit"),
    path("about/", views.about, name="about"),
    path("logout/", views.logout_view, name="logout"),
]
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/success/<str:order_number>/", views.checkout_success, name="checkout_success"),
    path("orders/", views.order_history, name="order_history"),
    path("orders/<str:order_number>/", views.order_detail, name="order_detail"),
    path("mpesa/callback/", views.mpesa_callback, name="mpesa_callback"),
    path("payment-status/<str:order_number>/", views.payment_status, name="payment_status"),
    path("add-to-cart/<int:variant_id>/", views.add_to_cart, name="add_to_cart"),
    path(
        "update-cart-item/<int:item_id>/",
        views.update_cart_item,
        name="update_cart_item",
    ),
    path(
        "remove-cart-item/<int:item_id>/",
        views.remove_cart_item,
        name="remove_cart_item",
    ),
]
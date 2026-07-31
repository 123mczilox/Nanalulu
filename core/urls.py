from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("shop/", views.shop, name="shop"),
    # path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("contact/", views.contact, name="contact"),
    
]
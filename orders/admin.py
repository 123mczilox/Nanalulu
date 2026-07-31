from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, Payment
# Register your models here.

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at", "updated_at")
    search_fields = ("user__username",)
    ordering = ("-created_at",)
   

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "variant",
        "quantity",
        "total_price",
    )

    search_fields = (
        "variant__product__name",
    )

    list_filter = (
        "variant__product__brand",
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "user",
        "status",
        "payment_status",
        "total_amount",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_status",
    )

    search_fields = (
        "order_number",
        "user__username",
        "phone_number",
    )

    readonly_fields = (
        "order_number",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "variant",
        "quantity",
        "price",
        "subtotal",
    )

    search_fields = (
        "order__order_number",
        "variant__product__name",
    )

    ordering = ("order",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "payment_method",
        "amount",
        "status",
        "transaction_id",
        "paid_at",
    )

    list_filter = (
        "payment_method",
        "status",
    )

    search_fields = (
        "order__order_number",
        "transaction_id",
    )

    ordering = ("-created_at",)

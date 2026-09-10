import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from products.models import ProductVariant

from .models import Cart, CartItem, Order, OrderItem, Payment
from .mpesa import send_stk_push
# Create your views here.

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=request.user
        )
        return cart

    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    cart, created = Cart.objects.get_or_create(
        session_key=session_key,
        user=None,
    )

    return cart

# ----------------------- add to cart view ------------------

def add_to_cart(request, variant_id):
    variant = get_object_or_404(
        ProductVariant,
        id=variant_id,
    )

    if not variant.is_available:
        messages.error(
            request,
            "This product is currently unavailable."
        )
        return redirect("product_detail", slug=variant.product.slug)

    if variant.stock_quantity <= 0:
        messages.error(
            request,
            "Sorry, this product is out of stock."
        )
        return redirect("product_detail", slug=variant.product.slug)

    cart = get_or_create_cart(request)

    quantity = int(request.POST.get("quantity", 1))

    if quantity < 1:
        quantity = 1

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        variant=variant,
        defaults={
            "quantity": quantity,
        },
    )

    if not created:
        new_quantity = cart_item.quantity + quantity

        if new_quantity > variant.stock_quantity:
            messages.error(
                request,
                f"Only {variant.stock_quantity} items are available."
            )
            return redirect(
                "product_detail",
                slug=variant.product.slug
            )

        cart_item.quantity = new_quantity
        cart_item.save()

    messages.success(
        request,
        f"{variant.product.name} ({variant.volume}) added to your cart."
    )

    return redirect("orders:cart")
# ----------------------- view cart ------------------
def cart(request):
    cart = get_or_create_cart(request)

    items = cart.items.select_related(
        "variant",
        "variant__product",
    )

    total = sum(
        item.total_price
        for item in items
    )

    context = {
        "cart": cart,
        "items": items,
        "total": total,
    }

    return render(
        request,
        "core/cart.html",
        context,
    )
# --------------update cart item quantity ----------------
def update_cart_item(request, item_id):

    if request.method == "POST":

        cart_item = get_object_or_404(
            CartItem,
            id=item_id
        )

        quantity = int(request.POST.get("quantity", 1))

        if quantity < 1:
            messages.error(
                request,
                "Quantity must be at least 1."
            )
            return redirect("orders:cart")

        if quantity > cart_item.variant.stock_quantity:
            messages.error(
                request,
                f"Only {cart_item.variant.stock_quantity} "
                f"items are available."
            )
            return redirect("orders:cart")

        cart_item.quantity = quantity
        cart_item.save()

        messages.success(
            request,
            "Cart updated successfully."
        )

    return redirect("orders:cart")
# ------------------- remove cart item -------------------
def remove_cart_item(request, item_id):
    if request.method != "POST":
        return redirect("orders:cart")

    cart = get_or_create_cart(request)

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart,
    )

    item.delete()

    messages.success(
        request,
        "Item removed from your cart."
    )

    return redirect("orders:cart")


# ----------------------- checkout ------------------
def checkout(request):
    cart = get_or_create_cart(request)

    items = cart.items.select_related(
        "variant",
        "variant__product",
    )

    if not items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("orders:cart")

    if request.method == "POST":
        recipient_name = request.POST.get("recipient_name", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        delivery_address = request.POST.get("delivery_address", "").strip()
        payment_method = request.POST.get("payment_method", "").strip()

        # Validate required fields
        errors = []
        if not recipient_name:
            errors.append("Recipient name is required.")
        if not phone_number:
            errors.append("Phone number is required.")
        if not delivery_address:
            errors.append("Delivery address is required.")

        valid_methods = {"mpesa", "cash"}
        if payment_method not in valid_methods:
            errors.append("Please select a valid payment method.")

        # Ensure stock availability for all items
        for ci in items:
            if ci.quantity > ci.variant.stock_quantity:
                errors.append(
                    f"Only {ci.variant.stock_quantity} units of {ci.variant.product.name} ({ci.variant.volume}) are available."
                )

        if errors:
            for e in errors:
                messages.error(request, e)
            # re-render with previously entered data
            context = {
                "cart": cart,
                "items": items,
                "total": sum(item.total_price for item in items),
                "recipient_name": recipient_name,
                "phone_number": phone_number,
                "delivery_address": delivery_address,
                "payment_method": payment_method,
            }
            return render(request, "core/checkout.html", context)
        # All validation passed; create Order, OrderItems and Payment atomically
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    cart=cart,
                    recipient_name=recipient_name,
                    phone_number=phone_number,
                    delivery_address=delivery_address,
                    total_amount=0,
                    payment_status="pending",
                )

                total = 0
                for ci in items:
                    variant = ProductVariant.objects.select_for_update().get(
                        pk=ci.variant_id
                    )

                    if not variant.is_available or ci.quantity > variant.stock_quantity:
                        raise ValueError(
                            f"Only {variant.stock_quantity} units of "
                            f"{variant.product.name} ({variant.volume}) are available."
                        )

                    price = variant.price
                    subtotal = price * ci.quantity
                    OrderItem.objects.create(
                        order=order,
                        variant=variant,
                        price=price,
                        quantity=ci.quantity,
                        subtotal=subtotal,
                    )
                    variant.stock_quantity -= ci.quantity
                    variant.save(update_fields=["stock_quantity", "updated_at"])
                    total += subtotal

                order.total_amount = total
                order.save()

                payment = Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    transaction_id=None,
                    amount=order.total_amount,
                    status="pending",
                )

                if payment_method == "mpesa":
                    try:
                        response = send_stk_push(
                            phone_number=phone_number,
                            amount=int(order.total_amount),
                            account_reference=f"Order {order.order_number}",
                        )
                        checkout_request_id = response.get("CheckoutRequestID")
                        if checkout_request_id:
                            payment.transaction_id = checkout_request_id
                            payment.save(update_fields=["transaction_id"])
                        messages.success(
                            request,
                            "M-Pesa payment request sent to your phone. Please complete the prompt.",
                        )
                    except Exception:
                        raise RuntimeError(
                            "M-Pesa payment request failed. Please try again."
                        )

                # Clear cart items only after successful creation
                cart.items.all().delete()

        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "core/checkout.html", {"cart": cart, "items": items})
        except RuntimeError as exc:
            messages.error(request, str(exc))
            return render(request, "core/checkout.html", {"cart": cart, "items": items})
        except Exception:
            messages.error(
                request,
                "An error occurred while creating your order. Please try again.",
            )
            return render(request, "core/checkout.html", {"cart": cart, "items": items})

        if payment_method == "mpesa":
            return redirect("orders:checkout_success", order_number=order.order_number)

        messages.success(
            request,
            "Order placed. We will contact you to confirm cash-on-delivery details."
            if payment_method == "cash"
            else "Order placed successfully.",
        )
        return redirect("orders:checkout_success", order_number=order.order_number)

    total = sum(item.total_price for item in items)

    context = {
        "cart": cart,
        "items": items,
        "total": total,
    }

    return render(request, "core/checkout.html", context)

# --------------------mpesa callback view------------------------
@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (TypeError, ValueError):
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid payload"}, status=400)

    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
    callback_amount = next(
        (
            item.get("Value")
            for item in callback_metadata
            if item.get("Name") == "Amount"
        ),
        None,
    )
    mpesa_receipt_number = next(
        (
            item.get("Value")
            for item in callback_metadata
            if item.get("Name") == "MpesaReceiptNumber"
        ),
        None,
    )

    with transaction.atomic():
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .filter(transaction_id=checkout_request_id)
            .first()
        )
        if payment and payment.status == "pending":
            if result_code == 0:
                try:
                    callback_amount = Decimal(str(callback_amount))
                except (InvalidOperation, TypeError):
                    callback_amount = None

                if callback_amount != payment.amount:
                    return JsonResponse(
                        {"ResultCode": 1, "ResultDesc": "Payment amount mismatch"},
                        status=400,
                    )

                payment.status = "successful"
                payment.paid_at = timezone.now()
                payment.mpesa_receipt_number = mpesa_receipt_number
                payment.save(
                    update_fields=[
                        "status",
                        "paid_at",
                        "mpesa_receipt_number",
                        "updated_at",
                    ]
                )

                payment.order.payment_status = "paid"
                payment.order.status = "confirmed"
                payment.order.save(update_fields=["payment_status", "status", "updated_at"])
            else:
                for item in payment.order.items.select_related("variant"):
                    variant = ProductVariant.objects.select_for_update().get(
                        pk=item.variant_id
                    )
                    variant.stock_quantity += item.quantity
                    variant.save(update_fields=["stock_quantity", "updated_at"])

                payment.status = "failed"
                payment.save(update_fields=["status", "updated_at"])
                payment.order.payment_status = "failed"
                payment.order.status = "cancelled"
                payment.order.save(update_fields=["payment_status", "status", "updated_at"])

    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"}, status=200)


def payment_status(request, order_number):
    order = get_object_or_404(
        Order.objects.select_related("payment", "cart"),
        order_number=order_number,
    )

    if order.user_id:
        if not request.user.is_authenticated or request.user.id != order.user_id:
            return JsonResponse({"detail": "Not found."}, status=404)
    elif order.cart and order.cart.session_key != request.session.session_key:
        return JsonResponse({"detail": "Not found."}, status=404)

    payment = order.payment
    return JsonResponse(
        {
            "status": payment.status,
            "receipt_number": payment.mpesa_receipt_number,
            "order_status": order.status,
        }
    )


def checkout_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    return render(request, "core/checkout_success.html", {"order": order})


@login_required
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .select_related("payment")
        .order_by("-created_at")
    )

    return render(request, "core/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.filter(user=request.user)
        .select_related("payment")
        .prefetch_related("items__variant__product"),
        order_number=order_number,
    )

    return render(request, "core/order_detail.html", {"order": order})
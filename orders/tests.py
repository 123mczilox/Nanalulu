import json

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from products.models import Store, Category, Brand, Product, ProductVariant
from .models import Cart, CartItem, Order, OrderItem, Payment


class CheckoutTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="pass")

        self.store = Store.objects.create(
            name="S", phone_number="0712345678", address="addr", county="C", opening_time="08:00", closing_time="18:00"
        )

        self.category = Category.objects.create(name="Cat")
        self.brand = Brand.objects.create(name="BR")

        self.product = Product.objects.create(name="Prod", store=self.store, category=self.category, brand=self.brand)

        self.variant = ProductVariant.objects.create(product=self.product, price=100, volume='500ml', stock_quantity=10)

        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, variant=self.variant, quantity=2)

    def test_checkout_creates_order_and_clears_cart(self):
        logged = self.client.login(username="tester", password="pass")
        self.assertTrue(logged)

        url = reverse('orders:checkout')

        data = {
            'recipient_name': 'Alice',
            'phone_number': '0711000000',
            'delivery_address': '123 Street',
            'payment_method': 'cash',
        }

        resp = self.client.post(url, data, follow=True)

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(OrderItem.objects.count(), 1)
        self.assertEqual(order.total_amount, self.variant.price * self.cart_item.quantity)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 8)
        self.assertEqual(Payment.objects.get(order=order).status, "pending")

        # Cart should be cleared
        self.assertEqual(self.cart.items.count(), 0)

    def place_cash_order(self):
        self.client.login(username="tester", password="pass")
        self.client.post(
            reverse("orders:checkout"),
            {
                "recipient_name": "Alice",
                "phone_number": "0711000000",
                "delivery_address": "123 Street",
                "payment_method": "cash",
            },
        )
        return Order.objects.get()

    def test_successful_mpesa_callback_marks_payment_paid(self):
        order = self.place_cash_order()
        payment = Payment.objects.get(order=order)
        payment.transaction_id = "ws_CO_123"
        payment.save(update_fields=["transaction_id"])

        response = self.client.post(
            reverse("orders:mpesa_callback"),
            data=json.dumps({
                "Body": {
                    "stkCallback": {
                        "ResultCode": 0,
                        "CheckoutRequestID": "ws_CO_123",
                        "CallbackMetadata": {
                            "Item": [
                                {"Name": "Amount", "Value": 200},
                                {"Name": "MpesaReceiptNumber", "Value": "SHX1234567"},
                            ],
                        },
                    },
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, "successful")
        self.assertEqual(payment.mpesa_receipt_number, "SHX1234567")
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.status, "confirmed")

        duplicate_response = self.client.post(
            reverse("orders:mpesa_callback"),
            data=json.dumps({
                "Body": {
                    "stkCallback": {
                        "ResultCode": 0,
                        "CheckoutRequestID": "ws_CO_123",
                        "CallbackMetadata": {
                            "Item": [
                                {"Name": "MpesaReceiptNumber", "Value": "DIFFERENT"},
                            ],
                        },
                    },
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(duplicate_response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.mpesa_receipt_number, "SHX1234567")

        status_response = self.client.get(
            reverse(
                "orders:payment_status",
                kwargs={"order_number": order.order_number},
            )
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "successful")
        self.assertEqual(status_response.json()["receipt_number"], "SHX1234567")

    def test_failed_mpesa_callback_releases_reserved_stock(self):
        order = self.place_cash_order()
        payment = Payment.objects.get(order=order)
        payment.transaction_id = "ws_CO_456"
        payment.save(update_fields=["transaction_id"])

        self.client.post(
            reverse("orders:mpesa_callback"),
            data=json.dumps({
                "Body": {
                    "stkCallback": {
                        "ResultCode": 1032,
                        "CheckoutRequestID": "ws_CO_456",
                    },
                },
            }),
            content_type="application/json",
        )

        payment.refresh_from_db()
        order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(payment.status, "failed")
        self.assertEqual(order.payment_status, "failed")
        self.assertEqual(order.status, "cancelled")
        self.assertEqual(self.variant.stock_quantity, 10)

    def test_successful_callback_rejects_amount_mismatch(self):
        order = self.place_cash_order()
        payment = Payment.objects.get(order=order)
        payment.transaction_id = "ws_CO_mismatch"
        payment.save(update_fields=["transaction_id"])

        response = self.client.post(
            reverse("orders:mpesa_callback"),
            data=json.dumps({
                "Body": {
                    "stkCallback": {
                        "ResultCode": 0,
                        "CheckoutRequestID": "ws_CO_mismatch",
                        "CallbackMetadata": {
                            "Item": [{"Name": "Amount", "Value": 1}],
                        },
                    },
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        payment.refresh_from_db()
        self.assertEqual(payment.status, "pending")

    def test_mpesa_callback_requires_post(self):
        response = self.client.get(reverse("orders:mpesa_callback"))

        self.assertEqual(response.status_code, 405)

    def test_authenticated_customer_can_view_order_history_and_details(self):
        order = self.place_cash_order()
        payment = Payment.objects.get(order=order)
        payment.status = "successful"
        payment.mpesa_receipt_number = "SHX9876543"
        payment.save(update_fields=["status", "mpesa_receipt_number"])

        history_response = self.client.get(reverse("orders:order_history"))
        detail_response = self.client.get(
            reverse(
                "orders:order_detail",
                kwargs={"order_number": order.order_number},
            )
        )

        self.assertEqual(history_response.status_code, 200)
        self.assertContains(history_response, order.order_number)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "SHX9876543")

    def test_order_history_requires_login(self):
        response = self.client.get(reverse("orders:order_history"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_customer_cannot_view_another_customers_order(self):
        other_user = User.objects.create_user(
            username="other-customer",
            password="pass",
        )
        other_order = Order.objects.create(
            user=other_user,
            recipient_name="Other Customer",
            phone_number="0711222333",
            delivery_address="Other Address",
            total_amount=100,
        )
        Payment.objects.create(order=other_order, amount=100)

        self.client.login(username="tester", password="pass")
        response = self.client.get(
            reverse(
                "orders:order_detail",
                kwargs={"order_number": other_order.order_number},
            )
        )

        self.assertEqual(response.status_code, 404)
from django.test import TestCase

# Create your tests here.

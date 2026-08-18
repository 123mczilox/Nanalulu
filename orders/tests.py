from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from products.models import Store, Category, Brand, Product, ProductVariant
from .models import Cart, CartItem, Order, OrderItem


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

        # Cart should be cleared
        self.assertEqual(self.cart.items.count(), 0)
from django.test import TestCase

# Create your tests here.

from products.models import ProductVariant

class SessionCart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')

        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, variant, quantity=1):
        variant_id = str(variant.id)
        if variant_id in self.cart:
            self.cart[variant_id]['quantity'] += quantity
        else:
            self.cart[variant_id] = {'quantity': quantity}
        self.save()

    def save(self):
        self.session.modified = True       
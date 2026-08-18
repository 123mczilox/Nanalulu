from .models import Cart


def cart_item_count(request):
    """Return number of items in the current cart for navbar badge.

    Does not create new cart objects; returns 0 when none found.
    """
    count = 0

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = cart.items.count()
        return {"cart_item_count": count}

    session_key = request.session.session_key
    if not session_key:
        return {"cart_item_count": 0}

    cart = Cart.objects.filter(session_key=session_key, user=None).first()
    if cart:
        count = cart.items.count()

    return {"cart_item_count": count}

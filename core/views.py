from django.shortcuts import render
from products.models import Product

def home(request):
    products = Product.objects.filter(
        is_active=True,
        is_featured=True
    )

    context = {
        "products": products,
    }

    return render(request, "core/home.html", context)

def shop(request):
    products = Product.objects.filter(is_active=True)

    context = {
        "products": products,
    }

    return render(request, "core/shop.html", context)

def contact(request):
    return render(request, "core/contact.html")
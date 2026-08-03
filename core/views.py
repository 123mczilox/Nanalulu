from django.shortcuts import get_object_or_404, render
from products.models import Category, Product
from django.db.models import Q

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
    categories = Category.objects.filter(is_active=True)
    query = request.GET.get("q")
    category = request.GET.get("category")

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)|
            Q(brand__name__icontains=query)
        )

    if category:
        products = products.filter(category_id=category)

    context = {
        "products": products,
        "categories": categories,
    }

    return render(request, "core/shop.html", context)

def contact(request):
    return render(request, "core/contact.html")

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related(
            "category",
            "brand",
            "store"

            ).prefetch_related(
                "images",
                "variants"
            ),
        slug=slug,
        is_active=True
    )

    context = {
        "product": product,
    }

    return render(request, "core/product_detail.html", context)
import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, redirect, render
from products.models import Category, Product
from django.db.models import Q

from .forms import ContactForm

logger = logging.getLogger(__name__)


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
    form = ContactForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        subject = form.cleaned_data["subject"]
        message = form.cleaned_data["message"]
        email_body = f"From: {name} <{email}>\n\n{message}"

        try:
            email_message = EmailMessage(
                subject=f"[Liquor Store A Contact] {subject}",
                body=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.CONTACT_EMAIL_TO],
                reply_to=[email],
            )
            sent_count = email_message.send(fail_silently=False)
        except Exception:
            logger.exception("Failed to send a contact form message.")
            messages.error(
                request,
                "We couldn't send your message right now. Please try again later or email us directly.",
            )
        else:
            if sent_count == 1:
                if settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend":
                    success_message = (
                        "Your message was written to the development server console. "
                        "Configure SMTP to deliver it by email."
                    )
                else:
                    success_message = (
                        "Thanks for contacting us. Your message has been sent."
                    )
                messages.success(
                    request,
                    success_message,
                )
                return redirect("contact")

            logger.error("Contact form email backend did not send the message.")
            messages.error(
                request,
                "We couldn't send your message right now. Please try again later or email us directly.",
            )

    return render(request, "core/contact.html", {"form": form})

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
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def register(request):

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("profile")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect(
                request.POST.get("next") or request.GET.get("next") or "profile"
            )

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")

def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("home")


@login_required
def profile(request):
    orders = request.user.orders.select_related("payment").order_by("-created_at")
    context = {
        "orders": orders[:5],
        "order_count": orders.count(),
        "pending_count": orders.filter(payment_status="pending").count(),
        "paid_count": orders.filter(payment_status="paid").count(),
    }
    return render(request, "accounts/profile.html", context)
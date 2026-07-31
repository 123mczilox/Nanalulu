from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import RegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def register(request):

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")

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
            return redirect("/")

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")

def logout_view(request):
    return HttpResponse("Logout Page")


def profile(request):
    return HttpResponse("Profile Page")
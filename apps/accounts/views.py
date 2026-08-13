from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

from .forms import RegisterForm


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            messages.success(request, "Account created successfully.")

            login(request, user)

            return redirect("accounts:dashboard")

    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


def login_view(request):

    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            login(request, form.get_user())

            return redirect("accounts:dashboard")

    return render(
        request,
        "accounts/login.html",
        {"form": form},
    )


def logout_view(request):

    logout(request)

    return redirect("accounts:login")


def dashboard(request):

    if not request.user.is_authenticated:
        return redirect("accounts:login")

    return render(
        request,
        "accounts/dashboard.html",
    )
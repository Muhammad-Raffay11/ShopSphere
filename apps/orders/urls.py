from django.urls import path

from . import views


app_name = "orders"


urlpatterns = [
    path(
        "checkout/",
        views.checkout,
        name="checkout",
    ),

    path(
        "stripe/webhook/",
        views.stripe_webhook,
        name="stripe_webhook",
    ),

    path(
        "payment-success/<str:order_number>/",
        views.payment_success,
        name="payment_success",
    ),

    path(
        "payment-cancelled/<str:order_number>/",
        views.payment_cancelled,
        name="payment_cancelled",
    ),

    path(
        "success/<str:order_number>/",
        views.order_success,
        name="success",
    ),

    path(
        "",
        views.order_list,
        name="list",
    ),

    path(
        "<str:order_number>/cancel/",
        views.cancel_order,
        name="cancel",
    ),

    path(
        "<str:order_number>/",
        views.order_detail,
        name="detail",
    ),
]
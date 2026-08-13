import stripe

from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(
    order,
    request,
):
    success_url = request.build_absolute_uri(
        f"/orders/payment-success/{order.order_number}/"
    )

    cancel_url = request.build_absolute_uri(
        f"/orders/payment-cancelled/{order.order_number}/"
    )

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],

        mode="payment",

        line_items=[
            {
                "price_data": {
                    "currency": "pkr",

                    "product_data": {
                        "name": item.product_name,
                    },

                    "unit_amount": int(
                        item.price * 100
                    ),
                },

                "quantity": item.quantity,
            }

            for item in order.items.all()
        ],

        metadata={
            "order_number": order.order_number,
        },

        success_url=success_url,

        cancel_url=cancel_url,
    )

    return session
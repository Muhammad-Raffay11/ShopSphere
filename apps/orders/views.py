import uuid
import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .stripe_utils import create_checkout_session
from apps.cart.models import Cart
from .models import Order, OrderItem
from django.http import JsonResponse


@login_required
def checkout(request):

    cart = get_object_or_404(
        Cart.objects.prefetch_related(
            "items__product"
        ),
        user=request.user,
    )

    items = cart.items.all()

    if not items.exists():
        return redirect("cart:detail")

    subtotal = cart.subtotal

    # For now, shipping is free.
    shipping_cost = 0

    total = subtotal + shipping_cost

    if request.method == "POST":

        payment_method = request.POST.get(
            "payment_method",
            "cod",
        )

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        city = request.POST.get(
            "city",
            ""
        ).strip()

        postal_code = request.POST.get(
            "postal_code",
            ""
        ).strip()


        if payment_method not in ["cod", "stripe"]:

          payment_method = "cod"
        


        if not all(
            [
                full_name,
                phone,
                address,
                city,
                postal_code,
                payment_method,
            ]
        ):
            context = {
                "cart": cart,
                "items": items,
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "total": total,
                "error": "Please fill in all delivery fields.",
            }

            return render(
                request,
                "orders/checkout.html",
                context,
            )

        order_number = (
            f"SS-{uuid.uuid4().hex[:10].upper()}"
        )

        with transaction.atomic():

            # Check stock and lock products
            for cart_item in items:

                product = cart_item.product

                if not product.is_available:
                    context = {
                        "cart": cart,
                        "items": items,
                        "subtotal": subtotal,
                        "shipping_cost": shipping_cost,
                        "total": total,
                        "error": (
                            f"{product.name} is currently unavailable."
                        ),
                    }

                    return render(
                        request,
                        "orders/checkout.html",
                        context,
                    )

                if cart_item.quantity > product.stock_quantity:
                    context = {
                        "cart": cart,
                        "items": items,
                        "subtotal": subtotal,
                        "shipping_cost": shipping_cost,
                        "total": total,
                        "error": (
                            f"Only {product.stock_quantity} units "
                            f"of {product.name} are available."
                        ),
                    }

                    return render(
                        request,
                        "orders/checkout.html",
                        context,
                    )

            # Create order
            order = Order.objects.create(
                user=request.user,
                order_number=order_number,
                full_name=full_name,
                phone=phone,
                address=address,
                city=city,
                postal_code=postal_code,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                total=total,
                status="pending",
                payment_status="pending",
            )

            # Create order items and decrease stock
            for cart_item in items:

                product = cart_item.product

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    price=product.price,
                    quantity=cart_item.quantity,
                    subtotal=cart_item.subtotal,
                )

                product.stock_quantity -= cart_item.quantity

                # Automatically mark unavailable when stock reaches zero
                if product.stock_quantity == 0:
                    product.is_available = False

                product.save(
                    update_fields=[
                        "stock_quantity",
                        "is_available",
                        "updated_at",
                    ]
                )

            # Empty customer's cart
            cart.items.all().delete()


            if payment_method == "stripe":

                session = create_checkout_session(
                    order,
                    request,
                )

                return redirect(
                    session.url
                )

            return redirect(
                "orders:success",
                order_number=order.order_number,
            )

    

    context = {
        "cart": cart,
        "items": items,
        "subtotal": subtotal,
        "shipping_cost": shipping_cost,
        "total": total,
    }

    return render(
        request,
        "orders/checkout.html",
        context,
    )


@login_required
def order_success(request, order_number):

    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    return render(
        request,
        "orders/order_success.html",
        {
            "order": order,
        },
    )


@login_required
def order_list(request):

    orders = Order.objects.filter(
        user=request.user
    )

    return render(
        request,
        "orders/order_list.html",
        {
            "orders": orders,
        },
    )


@login_required
def order_detail(request, order_number):

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items"
        ),
        order_number=order_number,
        user=request.user,
    )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
        },
    )


@login_required
def cancel_order(request, order_number):

    if request.method != "POST":
        return redirect(
            "orders:detail",
            order_number=order_number,
        )

    with transaction.atomic():

        order = get_object_or_404(
            Order.objects.select_for_update(),
            order_number=order_number,
            user=request.user,
        )

        # Customer can cancel only pending or confirmed orders
        if order.status not in ["pending", "confirmed"]:

            messages.error(
                request,
                f"This order cannot be cancelled because "
                f"its current status is {order.get_status_display()}.",
            )

            return redirect(
                "orders:detail",
                order_number=order.order_number,
            )

        # Prevent cancellation if already cancelled
        if order.status == "cancelled":

            messages.error(
                request,
                "This order has already been cancelled.",
            )

            return redirect(
                "orders:detail",
                order_number=order.order_number,
            )


        

        # Restore product stock
    for order_item in order.items.select_related("product"):

        product = order_item.product

        product.stock_quantity += order_item.quantity

        # Product becomes available again
        if product.stock_quantity > 0:
            product.is_available = True

        product.save(
            update_fields=[
                "stock_quantity",
                "is_available",
                "updated_at",
            ]
        )


    order.status = "cancelled"

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )




    messages.success(
        request,
        f"Order {order.order_number} has been cancelled successfully.",
    )

    return redirect(
        "orders:detail",
        order_number=order.order_number,
    )






@login_required
def payment_success(request, order_number):

    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    order.payment_status = "paid"
    order.status = "confirmed"

    order.save(
        update_fields=[
            "payment_status",
            "status",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Payment successful! Your order has been confirmed.",
    )

    return redirect(
        "orders:success",
        order_number=order.order_number,
    )



@login_required
def payment_cancelled(request, order_number):

    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    messages.warning(
        request,
        "Payment was cancelled. Your order is still pending.",
    )

    return redirect(
        "orders:detail",
        order_number=order.order_number,
    )


@csrf_exempt
def stripe_webhook(request):

    payload = request.body

    sig_header = request.META.get(
        "HTTP_STRIPE_SIGNATURE"
    )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        return JsonResponse(
            {"error": "Invalid payload"},
            status=400,
        )

    except stripe.error.SignatureVerificationError:
        return JsonResponse(
            {"error": "Invalid signature"},
            status=400,
        )

    if event["type"] == "checkout.session.completed":

        session = event["data"]["object"]

        metadata = session["metadata"]

        order_number = metadata["order_number"]

        order = get_object_or_404(
            Order,
            order_number=order_number,
        )

        if order.payment_status != "paid":

            order.payment_status = "paid"
            order.status = "confirmed"

            order.save(
                update_fields=[
                    "payment_status",
                    "status",
                    "updated_at",
                ]
            )

    return JsonResponse(
        {"status": "success"}
    )
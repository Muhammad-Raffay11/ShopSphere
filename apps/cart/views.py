from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import Product

from .models import Cart, CartItem


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    items = cart.items.select_related("product")

    context = {
        "cart": cart,
        "items": items,
    }

    return render(
        request,
        "cart/cart_detail.html",
        context,
    )


@login_required
def add_to_cart(request, product_id):

    if request.method != "POST":
        return redirect("catalog:product_detail", product_id)

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    # Check stock before creating CartItem
    if product.stock_quantity <= 0:

        messages.error(
            request,
            f"{product.name} is currently out of stock.",
        )

        return redirect(
            "catalog:product_detail",
            product.slug,
        )

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    item = CartItem.objects.filter(
        cart=cart,
        product=product,
    ).first()

    # Product is already in cart
    if item:

        if item.quantity >= product.stock_quantity:

            messages.error(
                request,
                f"Only {product.stock_quantity} units of "
                f"{product.name} are available.",
            )

            return redirect("cart:detail")

        item.quantity += 1
        item.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

        messages.success(
            request,
            f"{product.name} quantity increased.",
        )

    # Product is not yet in cart
    else:

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
        )

        messages.success(
            request,
            f"{product.name} added to your cart.",
        )

    return redirect("cart:detail")


@login_required
def update_cart_item(request, item_id):

    cart = get_object_or_404(
        Cart,
        user=request.user,
    )

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart,
    )

    if request.method != "POST":
        return redirect("cart:detail")

    quantity = request.POST.get(
        "quantity",
        "1",
    )

    try:
        quantity = int(quantity)

    except (ValueError, TypeError):

        messages.error(
            request,
            "Please enter a valid quantity.",
        )

        return redirect("cart:detail")

    # Quantity 0 means remove
    if quantity <= 0:

        item.delete()

        messages.success(
            request,
            "Item removed from your cart.",
        )

        return redirect("cart:detail")

    # Product unavailable
    if not item.product.is_available:

        item.delete()

        messages.error(
            request,
            f"{item.product.name} is no longer available.",
        )

        return redirect("cart:detail")

    # Stock validation
    if quantity > item.product.stock_quantity:

        messages.error(
            request,
            f"Only {item.product.stock_quantity} units "
            f"of {item.product.name} are available.",
        )

        return redirect("cart:detail")

    item.quantity = quantity

    item.save(
        update_fields=[
            "quantity",
            "updated_at",
        ]
    )

    messages.success(
        request,
        f"{item.product.name} quantity updated.",
    )

    return redirect("cart:detail")


@login_required
def remove_from_cart(request, item_id):

    cart = get_object_or_404(
        Cart,
        user=request.user,
    )

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart=cart,
    )

    if request.method != "POST":
        return redirect("cart:detail")

    item.delete()

    messages.success(
        request,
        "Item removed from your cart.",
    )

    return redirect("cart:detail")
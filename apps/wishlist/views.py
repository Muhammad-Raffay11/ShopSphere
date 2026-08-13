from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import Product
from apps.cart.models import Cart, CartItem

from .models import Wishlist, WishlistItem


@login_required
def wishlist_detail(request):
    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user
    )

    items = wishlist.items.select_related(
        "product"
    )

    context = {
        "wishlist": wishlist,
        "items": items,
    }

    return render(
        request,
        "wishlist/wishlist_detail.html",
        context,
    )


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True,
    )

    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user
    )

    WishlistItem.objects.get_or_create(
        wishlist=wishlist,
        product=product,
    )

    return redirect("wishlist:detail")


@login_required
def remove_from_wishlist(request, item_id):
    wishlist = get_object_or_404(
        Wishlist,
        user=request.user,
    )

    item = get_object_or_404(
        WishlistItem,
        id=item_id,
        wishlist=wishlist,
    )

    item.delete()

    return redirect("wishlist:detail")


@login_required
def move_to_cart(request, item_id):

    wishlist = get_object_or_404(
        Wishlist,
        user=request.user,
    )

    wishlist_item = get_object_or_404(
        WishlistItem,
        id=item_id,
        wishlist=wishlist,
    )

    product = wishlist_item.product

    # Product unavailable
    if not product.is_available:

        messages.error(
            request,
            f"{product.name} is no longer available.",
        )

        return redirect("wishlist:detail")

    # Product out of stock
    if product.stock_quantity <= 0:

        messages.error(
            request,
            f"{product.name} is currently out of stock.",
        )

        return redirect("wishlist:detail")

    cart, created = Cart.objects.get_or_create(
        user=request.user
    )

    cart_item = CartItem.objects.filter(
        cart=cart,
        product=product,
    ).first()

    # Already exists in cart
    if cart_item:

        if cart_item.quantity >= product.stock_quantity:

            messages.error(
                request,
                f"Only {product.stock_quantity} units "
                f"of {product.name} are available.",
            )

            return redirect("wishlist:detail")

        cart_item.quantity += 1

        cart_item.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )

    # New cart item
    else:

        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
        )

    # Remove from wishlist after successful transfer
    wishlist_item.delete()

    messages.success(
        request,
        f"{product.name} moved to your cart.",
    )

    return redirect("cart:detail")
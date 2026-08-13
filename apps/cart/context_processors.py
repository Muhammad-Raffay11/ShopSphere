from .models import Cart


def cart_count(request):
    if not request.user.is_authenticated:
        return {
            "cart_count": 0,
        }

    cart = Cart.objects.filter(
        user=request.user
    ).first()

    if not cart:
        return {
            "cart_count": 0,
        }

    count = sum(
        item.quantity
        for item in cart.items.all()
    )

    return {
        "cart_count": count,
    }
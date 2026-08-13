from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Brand, Category, Product


def home(request):
    categories = Category.objects.filter(is_active=True)
    latest_products = Product.objects.filter(
        is_available=True
    ).order_by("-created_at")[:8]

    context = {
        "categories": categories,
        "latest_products": latest_products,
    }

    return render(request, "catalog/home.html", context)


def product_list(request):
    products = Product.objects.filter(is_available=True)

    # Search
    query = request.GET.get("q", "").strip()

    if query:
        products = products.filter(
            name__icontains=query
        )

    # Category filter
    category_slug = request.GET.get("category", "").strip()

    if category_slug:
        products = products.filter(
            category__slug=category_slug
        )

    # Brand filter
    brand_slug = request.GET.get("brand", "").strip()

    if brand_slug:
        products = products.filter(
            brand__slug=brand_slug
        )

    # Sorting
    sort = request.GET.get("sort", "").strip()

    if sort == "price_low":
        products = products.order_by("price")

    elif sort == "price_high":
        products = products.order_by("-price")

    elif sort == "name":
        products = products.order_by("name")

    else:
        products = products.order_by("-created_at")

    # Pagination
    paginator = Paginator(products, 12)

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    categories = Category.objects.filter(is_active=True)

    brands = Brand.objects.filter(is_active=True)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "brands": brands,
        "query": query,
        "selected_category": category_slug,
        "selected_brand": brand_slug,
        "selected_sort": sort,
    }

    return render(
        request,
        "catalog/product_list.html",
        context,
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product,
        slug=slug,
        is_available=True,
    )

    gallery = product.images.all()

    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "gallery": gallery,
        },
    )
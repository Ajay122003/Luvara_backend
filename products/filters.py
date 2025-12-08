from django.db.models import Q, F, Case, When
from .models import Product

def product_filter(queryset, params):
    search = params.get("search")
    category = params.get("category")
    min_price = params.get("min_price")
    max_price = params.get("max_price")
    size = params.get("size")
    color = params.get("color")
    sort = params.get("sort")

    queryset = queryset.annotate(
        effective_price=Case(
            When(sale_price__isnull=False, then=F("sale_price")),
            default=F("price"),
        )
    )

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    if category:
        queryset = queryset.filter(category_id=category)

    if min_price:
        queryset = queryset.filter(effective_price__gte=min_price)

    if max_price:
        queryset = queryset.filter(effective_price__lte=max_price)

    if size:
        queryset = queryset.filter(sizes__icontains=size)

    if color:
        queryset = queryset.filter(colors__icontains=color)

    if sort == "price_low":
        queryset = queryset.order_by("effective_price")

    elif sort == "price_high":
        queryset = queryset.order_by("-effective_price")

    elif sort == "newest":
        queryset = queryset.order_by("-created_at")

    elif sort == "oldest":
        queryset = queryset.order_by("created_at")

    return queryset

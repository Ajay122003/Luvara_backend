from django.db.models import Q
from .models import Product

def product_filter(queryset, params):
    search = params.get("search")
    category = params.get("category")
    min_price = params.get("min_price")
    max_price = params.get("max_price")
    size = params.get("size")
    color = params.get("color")
    sort = params.get("sort")

    # ----------- SEARCH -----------
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # ----------- CATEGORY -----------
    if category:
        queryset = queryset.filter(category__id=category)

    # ----------- PRICE FILTER ----------- 
    if min_price:
        queryset = queryset.filter(price__gte=min_price)

    if max_price:
        queryset = queryset.filter(price__lte=max_price)

    # ----------- SIZE FILTER ----------- 
    if size:
        queryset = queryset.filter(sizes__icontains=size)

    # ----------- COLOR FILTER ----------- 
    if color:
        queryset = queryset.filter(colors__icontains=color)

    # ----------- SORTING -----------
    if sort == "price_low":
        queryset = queryset.order_by("price")

    elif sort == "price_high":
        queryset = queryset.order_by("-price")

    elif sort == "newest":
        queryset = queryset.order_by("-created_at")

    elif sort == "oldest":
        queryset = queryset.order_by("created_at")

    return queryset

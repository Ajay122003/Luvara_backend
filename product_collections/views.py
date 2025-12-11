from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404

from .models import Collection
from .serializers import CollectionListSerializer, CollectionDetailSerializer


class CollectionListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # optional: only active collections unless admin
        qs = Collection.objects.filter(is_active=True).order_by("-sort_order", "-created_at")
        serializer = CollectionListSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CollectionDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        collection = get_object_or_404(Collection, slug=slug, is_active=True)
        # paginate products inside collection
        products_qs = collection.products.filter(is_active=True).order_by("-created_at")
        paginator = PageNumberPagination()
        paginator.page_size = 12
        page = paginator.paginate_queryset(products_qs, request)
        # reuse product serializer (ProductSerializer expects context request)
        from products.serializers import ProductSerializer
        prod_ser = ProductSerializer(page, many=True, context={"request": request})
        # return both collection info + paginated products meta
        coll_ser = CollectionListSerializer(collection, context={"request": request})
        return paginator.get_paginated_response({
            "collection": coll_ser.data,
            "products": prod_ser.data
        })

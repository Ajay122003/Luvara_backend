from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Collection
from .serializers import (
    CollectionListSerializer,
    CollectionDetailSerializer
)


class CollectionListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Collection.objects.filter(is_active=True).order_by("sort_order")
        serializer = CollectionListSerializer(
            qs,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data, status=200)


class CollectionDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            collection = Collection.objects.get(slug=slug, is_active=True)
        except Collection.DoesNotExist:
            return Response({"error": "Collection not found"}, status=404)

        serializer = CollectionDetailSerializer(
            collection,
            context={"request": request}
        )
        return Response(serializer.data)

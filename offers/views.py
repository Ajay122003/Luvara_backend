from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from .models import Offer
from .serializers import *


# ---------------------------------
# PUBLIC OFFER LIST (User Side)
# ---------------------------------
class OfferListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()

        offers = Offer.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gt=now   # 🔥 STRICT DEADLINE
        ).order_by("-created_at")

        serializer = OfferSerializer(
            offers,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data, status=200)


# ---------------------------------
# PUBLIC OFFER DETAIL (SLUG BASED)
# ---------------------------------
class OfferDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        now = timezone.now()

        try:
            offer = Offer.objects.get(
                slug=slug,
                is_active=True,
                start_date__lte=now,
                end_date__gt=now   #  SAME STRICT CHECK
            )
        except Offer.DoesNotExist:
            return Response(
                {"error": "Offer not found"},
                status=404
            )

        serializer = OfferDetailSerializer(
            offer,
            context={"request": request}
        )
        return Response(serializer.data, status=200)

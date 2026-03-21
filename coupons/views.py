from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import CouponApplySerializer


class ApplyCouponAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponApplySerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.save()
            return Response(
                {
                    "message": "Coupon applied successfully",
                    "coupon": result["coupon"],
                    "discount": result["discount"],
                    "final_amount": result["final_amount"],
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import CouponApplySerializer

class ApplyCouponAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponApplySerializer(data=request.data)

        if serializer.is_valid():
            result = serializer.save()
            return Response({
                "message": "Coupon applied successfully",
                "discount": result["discount"],
                "final_amount": result["final_amount"]
            })

        return Response(serializer.errors, status=400)

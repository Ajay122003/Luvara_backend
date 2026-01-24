from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from .serializers import *
from .models import User
import logging
from django.db.models import Q
from products.models import Product
from categories.models import Category
from products.serializers import ProductSerializer
from categories.serializers import CategorySerializer

def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Account created. Please login to get OTP."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




logger = logging.getLogger(__name__)


class LoginSendOTPView(APIView):
    def post(self, request):
        serializer = LoginOTPRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]  # or however you store it

            send_otp_email(email, otp)  # ✅ THIS WAS MISSING

            return Response(
                {
                    "message": "OTP sent successfully",
                    "email": email
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginVerifyOTPView(APIView):
    throttle_scope = "otp"

    def post(self, request):
        serializer = LoginOTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = get_tokens(user)
            logger.info(f"User logged in via OTP: {user.email}")
            return Response(
                {"message": "Login successful", "tokens": tokens},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            if data.get("otp_required"):
                return Response(
                    {
                        "otp_required": True,
                        "email": data["email"]
                    },
                    status=200
                )

            tokens = get_tokens(data["user"])
            return Response(
                {"message": "Login successful", "tokens": tokens},
                status=200
            )

        return Response(serializer.errors, status=400)



class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "is_email_verified": user.is_email_verified,
        })



class LogoutView(APIView):
    # permission_classes = [IsAuthenticated]

    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"error": "Invalid or expired token"}, status=400)

        return Response({"message": "Logged out successfully"}, status=205)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Profile updated successfully"},
                status=200
            )
        return Response(serializer.errors, status=400)





class GlobalSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.GET.get("q", "").strip()

        if not query:
            return Response(
                {
                    "count": 0,
                    "products": []
                },
                status=status.HTTP_200_OK
            )

        # ✅ PRODUCT SEARCH (NAME + SKU + DESCRIPTION + CATEGORY + COLLECTION)
        products = (
            Product.objects
            .filter(
                Q(name__icontains=query) |                 # product name
                Q(sku__icontains=query) |                  # ✅ product number / SKU
                Q(description__icontains=query) |          # description
                Q(category__name__icontains=query) |       # category name
                Q(collections__name__icontains=query)      # ✅ collection name
            )
            .prefetch_related("images", "variants", "collections")
            .distinct()
        )

        product_data = ProductSerializer(
            products,
            many=True,
            context={"request": request}
        ).data

        return Response(
            {
                "count": len(product_data),
                "products": product_data
            },
            status=status.HTTP_200_OK
        )
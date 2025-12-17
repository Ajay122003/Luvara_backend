from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Address
from .serializers import AddressSerializer


class AddressListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # -----------------------------
    # GET → Profile page addresses
    # (ONLY saved addresses)
    # -----------------------------
    def get(self, request):
        addresses = Address.objects.filter(
            user=request.user,
            is_temporary=False   # 🔥 hide delivery-only addresses
        ).order_by("-id")

        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    # -----------------------------
    # POST → Add new saved address
    # (Profile page)
    # -----------------------------
    def post(self, request):
        serializer = AddressSerializer(data=request.data)

        if serializer.is_valid():
            is_default = request.data.get("is_default", False)

            # If setting new default → unset old default
            if is_default:
                Address.objects.filter(
                    user=request.user,
                    is_default=True
                ).update(is_default=False)

            # Save as permanent address
            serializer.save(
                user=request.user,
                is_default=is_default,
                is_temporary=False   # 🔥 profile address = permanent
            )

            # If first saved address → force default
            if Address.objects.filter(
                user=request.user,
                is_temporary=False
            ).count() == 1:
                serializer.instance.is_default = True
                serializer.instance.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Address.objects.get(pk=pk, user=user)
        except Address.DoesNotExist:
            return None

    # -----------------------------
    # UPDATE address
    # -----------------------------
    def put(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response(
                {"error": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AddressSerializer(
            address,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # -----------------------------
    # DELETE address
    # -----------------------------
    def delete(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response(
                {"error": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Optional safety: prevent deleting default address
        # if address.is_default:
        #     return Response(
        #         {"error": "Cannot delete default address"},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )

        address.delete()
        return Response(
            {"message": "Address deleted"},
            status=status.HTTP_200_OK
        )


class SetDefaultAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # -----------------------------
    # SET DEFAULT ADDRESS
    # -----------------------------
    def post(self, request, pk):
        try:
            address = Address.objects.get(
                pk=pk,
                user=request.user,
                is_temporary=False  # 🔥 only saved addresses
            )
        except Address.DoesNotExist:
            return Response(
                {"error": "Address not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        Address.objects.filter(
            user=request.user,
            is_default=True
        ).update(is_default=False)

        address.is_default = True
        address.save()

        return Response(
            {"message": "Default address updated"},
            status=status.HTTP_200_OK
        )

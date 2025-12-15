from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Address
from .serializers import AddressSerializer

class AddressListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
           is_default = request.data.get("is_default", False)

           if is_default:
              Address.objects.filter(
                 user=request.user, is_default=True
              ).update(is_default=False)

           serializer.save(user=request.user, is_default=is_default)

        # If first address → force default
           if Address.objects.filter(user=request.user).count() == 1:
               serializer.instance.is_default = True
               serializer.instance.save()

           return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)



class AddressDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Address.objects.get(pk=pk, user=user)
        except Address.DoesNotExist:
            return None

    def put(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"error": "Address not found"}, status=404)

        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"error": "Address not found"}, status=404)

        address.delete()
        return Response({"message": "Address deleted"}, status=200)

class SetDefaultAddressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            address = Address.objects.get(pk=pk, user=request.user)
        except Address.DoesNotExist:
            return Response({"error": "Address not found"}, status=404)

        Address.objects.filter(
            user=request.user, is_default=True
        ).update(is_default=False)

        address.is_default = True
        address.save()

        return Response({"message": "Default address updated"})

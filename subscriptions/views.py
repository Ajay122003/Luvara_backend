from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import SubscriberSerializer

class SubscribeView(APIView):
    def post(self, request):
        serializer = SubscriberSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Subscribed successfully!"}, status=200)

        return Response(serializer.errors, status=400)

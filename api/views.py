from django.shortcuts import render
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from knox.models import AuthToken
from knox.serializers import UserSerializer
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

# Create your views here.
@permission_classes(
    [
        AllowAny,
    ]
)
class register(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        if (
            request.data.get("username") != ""
            and request.data.get("password") != ""
        ):
            # try:
            user = User.objects.create_user(
                username=request.data.get("username"),
                password=request.data.get("password")
            )
            # except Exception as e:
            #     print(e)
            #     return Response("Username already used!!", status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {
                    "token": AuthToken.objects.create(user)[1],
                    "status": 200,
                }
            )
        return Response(
            "Username and password are required fields", status=status.HTTP_400_BAD_REQUEST
        )

@permission_classes(
    [
        AllowAny,
    ]
)
class login(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        user = authenticate(
            username=request.data.get("username"), password=request.data.get("password")
        )
        if user is not None:
            return Response(
                {
                    "user": UserSerializer(
                        user, context=self.get_serializer_context()
                    ).data,
                    "token": AuthToken.objects.create(user)[1],
                    "status": 200,
                }
            )
        else:
            return Response(
                "Wrong Credentials! Please try again.", status=status.HTTP_403_FORBIDDEN
            )
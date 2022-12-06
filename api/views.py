from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from knox.models import AuthToken
from knox.serializers import UserSerializer
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import TransactionSerializer, WalletSerializer, LabelSerializer
from .models import Transaction, Wallet, Label
from django.utils import timezone

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


@permission_classes([IsAuthenticated])
class create_transaction(generics.GenericAPIView):
    serializer_class = TransactionSerializer

    def post(self, request):
        date_time = timezone.now()
        data = {
            "amount": request.data.get("amount"),
            "is_expense": request.data.get("is_expense", True),
            "wallet": request.data.get("wallet"),
            "date_time": date_time,
            # These will be used to crete data rich statistics for the user,
            "day": date_time.day,
            "week": date_time.day // 7 + 1,
            "month": date_time.month,
            "year": date_time.year
        }

        label_strings = request.data.get("labels")
        labels = []
        for label in label_strings:
            lbl = Label.objects.get(id=label, user=request.user)
            labels.append(lbl)
        
        data["wallet"] = Wallet.objects.get(id=data["wallet"], user=request.user)
        trxn = Transaction.objects.create(**data)
        trxn.labels.add(*labels)
        trxn.save()

        return Response({
            "success": True,
            "trxn": TransactionSerializer(trxn).data
        })

@permission_classes([IsAuthenticated])
class create_label(generics.GenericAPIView):
    serializer_class = LabelSerializer

    def post(self, request):
        date_time = timezone.now()
        data = {
            "name": request.data.get("name"),
            "description": request.data.get("description"),
            "created_on": date_time,
            "user": request.user,
            "color": request.data.get("color", "#fff"),
        }

        # TODO: Check if label of same name exists for the user
        label = Label.objects.create(**data)

        return Response({
            "success": True,
            "label": LabelSerializer(label).data
        })

@permission_classes([IsAuthenticated])
class create_wallet(generics.GenericAPIView):
    serializer_class = WalletSerializer

    def post(self, request):
        date_time = timezone.now()
        data = {
            "name": request.data.get("name"),
            "description": request.data.get("description"),
            "created_on": date_time,
            "user": request.user,
            "balance": 0,
        }

        # TODO: Check if wallet of same name exists for the user
        wallet = Wallet.objects.create(**data)

        return Response({
            "success": True,
            "wallet": WalletSerializer(wallet).data
        })

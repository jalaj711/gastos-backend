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
from django.db.models import Q
import operator
from functools import reduce


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
            "name": request.data.get("name"),
            "description": request.data.get("description", ""),
            "amount": request.data.get("amount"),
            "is_expense": request.data.get("is_expense", True),
            "wallet": request.data.get("wallet"),
            "date_time": date_time,
            "user": request.user,
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

        data["wallet"] = Wallet.objects.get(
            id=data["wallet"], user=request.user)
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
            "description": request.data.get("description", ""),
            "created_on": date_time,
            "user": request.user,
            "color": request.data.get("color", "#fff"),
        }

        try:
            Label.objects.get(user=request.user, name=data["name"])
            return Response({
                "success": False,
                "message": "Label with same name already exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Label.DoesNotExist:
            
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
            "description": request.data.get("description", ""),
            "created_on": date_time,
            "user": request.user,
            "balance": 0,
        }

        try:
            Wallet.objects.get(user=request.user, name=data["name"])
            return Response({
                "success": False,
                "message": "Wallet with same name already exists"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(**data)

            return Response({
                "success": True,
                "wallet": WalletSerializer(wallet).data
            })


@permission_classes([IsAuthenticated])
class get_transactions(generics.GenericAPIView):
    serializer_class = TransactionSerializer

    def get(self, request):

        # Extract Labels
        label_ids = []
        _labels = request.GET.get("labels", "").split(",")
        if len(_labels) > 0 and _labels[0] != "":
            label_ids = [int(i) for i in _labels]

        # Whether the labels selected are to be used as an union
        # search or an intersection set.

        # Union means: If labels A & B are selected, then the search
        # results should contain all trxns with the label A only, B
        # only and both A & B

        # Intersection means: If labels A & B are selected then the
        # search result should only contain trxns with both A & B.
        label_search_union = request.GET.get(
            "label_search_type_union", "true").capitalize() == True

        # Extract Wallets
        wallet_ids = []
        _wallets = request.GET.get("wallets", "").split(",")
        if len(_wallets) > 0 and _wallets[0] != "":
            wallet_ids = [int(i) for i in _wallets]

        # Extract Search string
        search_str = request.GET.get("search", "")

        # Build the filters
        search_filters = {
            "user": request.user
        }

        if len(wallet_ids) != 0:
            search_filters["wallet__id__in"] = wallet_ids

        if search_str != "":
            search_filters["name__contains"] = search_str

        if len(label_ids) != 0 and label_search_union:
            search_filters["labels__id__in"] = label_ids



        if len(label_ids) != 0 and not label_search_union:
            labels = [Q(labels__id=label) for label in label_ids]
            trxns = Transaction.objects.all().exclude(~Q(labels__id__in=label_ids))
            #.filter(
            #   reduce(operator.and_, labels)).order_by("-date_time")
            print(trxns, labels)
        else:
            print(search_filters)
            trxns = Transaction.objects.filter(
                **search_filters).distinct().order_by("-date_time")

        return Response({
            "success": True,
            "trxns": [TransactionSerializer(trxn).data for trxn in trxns]
        })


@permission_classes([IsAuthenticated])
class get_wallets(generics.GenericAPIView):
    serializer_class = WalletSerializer

    def get(self, request):
        wallets = Wallet.objects.filter(
            user=request.user).order_by("-created_on")

        return Response({
            "success": True,
            "wallets": [WalletSerializer(wallet).data for wallet in wallets]
        })


@permission_classes([IsAuthenticated])
class get_labels(generics.GenericAPIView):
    serializer_class = LabelSerializer

    def get(self, request):
        labels = Label.objects.filter(
            user=request.user).order_by("-created_on")

        return Response({
            "success": True,
            "labels": [LabelSerializer(wallet).data for wallet in labels]
        })

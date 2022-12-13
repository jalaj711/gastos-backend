from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response

from knox.models import AuthToken

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count

from api.serializers import TransactionSerializer, WalletSerializer, LabelSerializer, UserSerializer
from api.models import Transaction, Wallet, Label
from api.utils.serialize import _serialize

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
            try:
                user = User.objects.create_user(
                    username=request.data.get("username"),
                    password=request.data.get("password")
                )
            except Exception as e:
                return Response("Username already used!!", status=status.HTTP_400_BAD_REQUEST)

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
            data = UserSerializer(
                        user, context=self.get_serializer_context()
                    ).data
            data.update({
                "labels": user.label_set.all().values("id", "name", "color"),
                "wallets": user.wallet_set.all().values("id", "name", "balance")
            })
            return Response(
                {
                    "user_data": data,
                    "token": AuthToken.objects.create(user)[1],
                    "status": 200,
                }
            )
        else:
            return Response(
                "Wrong Credentials! Please try again.", status=status.HTTP_403_FORBIDDEN
            )


@permission_classes([IsAuthenticated])
class get_user_stats(generics.GenericAPIView):
    serializer_class = LabelSerializer

    def get(self, request):
        today = timezone.now()

        core_trxns = Transaction.objects.filter(user=request.user)
        this_year_filter = core_trxns.filter(year=today.year)
        this_month_filter = this_year_filter.filter(month=today.month)
        this_week_filter = this_month_filter.filter(week=today.day // 7 + 1)
        today_filter = this_month_filter.filter(day=today.day)

        data = {
            "user": UserSerializer(request.user).data,

            # TODO: Limit the number of responses in these queries
            "labels": _serialize(Label.objects.filter(user=request.user), LabelSerializer),
            "wallets": _serialize(Wallet.objects.filter(user=request.user), WalletSerializer),
            "transactions": {
                "today": today_filter.values("day").annotate(count=Count('id'), spent=Sum('amount')),
                "this_week": this_week_filter.values("week").annotate(count=Count('id'), spent=Sum('amount')),
                "this_month": this_month_filter.values("month").annotate(count=Count('id'), spent=Sum('amount')),
            },
            "daily": this_week_filter.values("day").annotate(count=Count('id'), spent=Sum('amount')),
            "weekly": this_month_filter.values("week").annotate(count=Count('id'), spent=Sum('amount')),
            "monthly": this_year_filter.values("month").annotate(count=Count('id'), spent=Sum('amount')),
            "recents": _serialize(core_trxns.order_by("-date_time")[:10], TransactionSerializer)
        }

        # Total amount spent by number of days
        # tr.objects.filter(month=12).values("day", "month", "year").annotate(spent=Sum('amount'))

        # Filter by date_time
        # tr.objects.filter(date_time__gt=tz.date(2022, 12, 06))

        return Response({
            "success": True,
            "data": data
        })
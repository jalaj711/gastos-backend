from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response

from knox.models import AuthToken

from calendar import Calendar

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import Round

from api.serializers import TransactionSerializer, WalletSerializer, LabelSerializer, UserSerializer
from api.models import Transaction, Wallet, Label
from api.utils.serialize import _serialize
from api.utils.week import get_wom_from_date
from api.utils.fill_empty_data import fill_empty_data


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
            and request.data.get("firstname") != ""
        ):
            try:
                user = User.objects.create_user(
                    username=request.data.get("username"),
                    password=request.data.get("password"),
                    first_name=request.data.get("firstname"),
                    last_name=request.data.get("lastname", ""),
                )
                w = Wallet.objects.create(
                    name="Wallet 1", description="The default wallet", user=user)

                data = UserSerializer(
                    user, context=self.get_serializer_context()
                ).data
                data.update({
                    "labels": [],
                    "wallets": [{"id": w.pk, "name": w.name, "balance": 0}]
                })
            except Exception as e:
                return Response({
                    "success": False,
                    "message": "Username already used!"}, status=status.HTTP_400_BAD_REQUEST)

            return Response(
                {
                    "token": AuthToken.objects.create(user)[1],
                    "user": data,
                    "success": True,
                }
            )
        return Response({
            "success": False,
            "message": "Username and password are required fields"}, status=status.HTTP_400_BAD_REQUEST
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
            try:
                labels = user.label_set.all().values("id", "name", "color")
            except Label.DoesNotExist:
                labels = []
            try:
                wallets = user.wallet_set.all().values("id", "name", "balance")
            except Wallet.DoesNotExist:
                wallets = []
            data.update({
                "labels":  labels,
                "wallets":  wallets
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
        this_year_filter = core_trxns.filter(year=today.year, is_expense=True)
        this_month_filter = this_year_filter.filter(month=today.month)
        today_filter = this_month_filter.filter(day=today.day)

        this_week = get_wom_from_date(today)
        this_week_filter = this_month_filter.filter(week=this_week)

        cal = Calendar().monthdayscalendar(today.year, today.month)
        try:
            while True:
                cal[this_week - 1].remove(0)
        except ValueError:
            pass
        data = {
            "user": UserSerializer(request.user).data,
            "transactions": {
                "today": fill_empty_data(today_filter.values("day").annotate(count=Count('id'), spent=Round(Sum('amount'), precision=2)), ["spent", "count"], "day", [0]),
                "this_week": fill_empty_data(this_week_filter.values("week").annotate(count=Count('id'), spent=Round(Sum('amount'), precision=2)), ["spent", "count"], "week", [0]),
                "this_month": fill_empty_data(this_month_filter.values("month").annotate(count=Count('id'), spent=Round(Sum('amount'), precision=2)), ["spent", "count"], "month", [0]),
            },
            "daily": fill_empty_data(this_week_filter.values("day", "month").annotate(count=Count('id'), spent=Round(Sum('amount'), precision=2)), ["spent", "count"], "day", range(cal[this_week - 1][0], cal[this_week - 1][-1] + 1)),
            "weekly": fill_empty_data(this_month_filter.values("week", "month").annotate(count=Count('id'), spent=Round(Sum('amount'), precision=2)), ["spent", "count"], "week", range(1, len(cal) + 1)),
            "monthly": fill_empty_data(this_year_filter.values("month", "year").annotate(count=Count('id'), spent=Round(Sum('amount'), precision=2)), ["spent", "count"], "month", range(1, 13)),
            "recents": _serialize(core_trxns.order_by("-date_time")[:10], TransactionSerializer)
        }

        return Response({
            "success": True,
            "data": data
        })

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response

from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import Round

from calendar import Calendar

from api.serializers import TransactionSerializer, WalletSerializer
from api.models import Transaction, Wallet
from api.utils.serialize import _serialize
from api.utils.week import get_wom_from_date
from api.utils.fill_empty_data import fill_empty_data

@permission_classes([IsAuthenticated])
class create(generics.GenericAPIView):
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
class update(generics.GenericAPIView):
    serializer_class = WalletSerializer

    def post(self, request):
        wallet_id = request.data.get("wallet", None)
        if (wallet_id is None):
            return Response({
                "success": False,
                "message": "Wallet ID is required for update"
            }, status=status.HTTP_400_BAD_REQUEST)


        new_data = request.data.get("new_data")
        if (new_data is None):
            return Response({
                "success": False,
                "message": "New data is required for update"
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_data.get("name", None) is None or new_data.get("name") == "":
            return Response({
                "success": False,
                "message": "Name cannot be empty"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = Wallet.objects.get(id=wallet_id, user=request.user)
        except Wallet.DoesNotExist:
            return Response({
                "success": False,
                "message": "Requested wallet not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if new_data.get("name") != wallet.name:
            try:
                Wallet.objects.get(user=request.user, name=new_data.get("name"))
                return Response({
                    "success": False,
                    "message": "Wallet with same name already exists"
                }, status=status.HTTP_400_BAD_REQUEST)
            except Wallet.DoesNotExist:
                wallet.name = new_data.get("name")

        if new_data.get("description", "") != wallet.description:
            wallet.description = new_data.get("description", "")

        wallet.save()
        return Response({
            "success": True,
            "wallet": WalletSerializer(wallet).data
        })

@permission_classes([IsAuthenticated])
class get(generics.GenericAPIView):
    serializer_class = WalletSerializer

    def get(self, request):
        wallets = Wallet.objects.filter(
            user=request.user).order_by("-created_on")

        return Response({
            "success": True,
            "wallets": [WalletSerializer(wallet).data for wallet in wallets]
        })



@permission_classes([IsAuthenticated])
class stats(generics.GenericAPIView):
    serializer_class = WalletSerializer

    def get(self, request):
        wallet = request.GET.get("wallet")

        if wallet is None:
            return Response({
                "success": False,
                "message": "Wallet is not provided"
            })

        try:
            wallet = Wallet.objects.get(id=wallet, user=request.user)
        except Wallet.DoesNotExist:
            return Response({
                "success": False,
                "message": "The requested wallet does not exist"
            })

        today = timezone.now()

        core_trxns = Transaction.objects.filter(
            user=request.user, wallet__id=wallet.id)
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
            "wallet": WalletSerializer(wallet).data,
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

        # Total amount spent by number of days
        # tr.objects.filter(month=12).values("day", "month", "year").annotate(spent=Sum('amount'))

        # Filter by date_time
        # tr.objects.filter(date_time__gt=tz.date(2022, 12, 06))

        return Response({
            "success": True,
            "data": data
        })

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response

from django.utils import timezone
from django.db.models import Sum, Count

from api.serializers import TransactionSerializer, WalletSerializer
from api.models import Transaction, Wallet
from api.utils.serialize import _serialize

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
        except wallet.DoesNotExist:
            return Response({
                "success": False,
                "message": "The requested wallet does not exist"
            })

        today = timezone.now()

        core_trxns = Transaction.objects.filter(
            user=request.user, wallet__id=wallet.id)
        this_year_filter = core_trxns.filter(year=today.year)
        this_month_filter = this_year_filter.filter(month=today.month)
        this_week_filter = this_month_filter.filter(week=today.day // 7 + 1)
        today_filter = this_month_filter.filter(day=today.day)

        data = {
            "wallet": WalletSerializer(wallet).data,
            "transactions": {
                "today": today_filter.values("day").annotate(count=Count('id'), spent=Sum('amount')),
                "this_week": this_week_filter.values("week").annotate(count=Count('id'), spent=Sum('amount')),
                "this_month": this_month_filter.values("month").annotate(count=Count('id'), spent=Sum('amount')),
            },
            "daily": this_week_filter.values("day").annotate(count=Count('id'), spent=Sum('amount')),
            "weekly": this_month_filter.values("week").annotate(count=Count('id'), spent=Sum('amount')),
            "monthly": this_year_filter.values("month").annotate(count=Count('id'), spent=Sum('amount')),

            # TODO: Limit the number of responses in this query
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

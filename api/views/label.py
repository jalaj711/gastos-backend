from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response

from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import Round

from calendar import Calendar

from api.serializers import TransactionSerializer, LabelSerializer
from api.models import Transaction, Label
from api.utils.serialize import _serialize
from api.utils.week import get_wom_from_date
from api.utils.fill_empty_data import fill_empty_data

@permission_classes([IsAuthenticated])
class create(generics.GenericAPIView):
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
class get(generics.GenericAPIView):
    serializer_class = LabelSerializer

    def get(self, request):
        labels = Label.objects.filter(
            user=request.user).order_by("-created_on")

        return Response({
            "success": True,
            "labels": [LabelSerializer(wallet).data for wallet in labels]
        })


@permission_classes([IsAuthenticated])
class stats(generics.GenericAPIView):
    serializer_class = LabelSerializer

    def get(self, request):
        label = request.GET.get("label")

        if label is None:
            return Response({
                "success": False,
                "message": "Label is not provided"
            })

        try:
            label = Label.objects.get(id=label, user=request.user)
        except Label.DoesNotExist:
            return Response({
                "success": False,
                "message": "The requested label does not exist"
            })

        today = timezone.now()

        core_trxns = Transaction.objects.filter(
            user=request.user, labels__id=label.id)
        this_year_filter = core_trxns.filter(year=today.year)
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
            "label": LabelSerializer(label).data,
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
        # tr.objects.filter(month=12).values("day", "month", "year").annotate(spent=Round(Sum('amount'), precision=2))

        # Filter by date_time
        # tr.objects.filter(date_time__gt=tz.date(2022, 12, 06))

        return Response({
            "success": True,
            "data": data
        })
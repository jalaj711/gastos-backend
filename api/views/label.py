from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response

from django.utils import timezone
from django.db.models import Sum, Count

from api.serializers import TransactionSerializer, LabelSerializer
from api.models import Transaction, Label
from api.utils.serialize import _serialize

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
        this_week_filter = this_month_filter.filter(week=today.day // 7 + 1)
        today_filter = this_month_filter.filter(day=today.day)

        data = {
            "label": LabelSerializer(label).data,
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
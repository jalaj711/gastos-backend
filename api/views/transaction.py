from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.response import Response

from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage

from api.serializers import TransactionSerializer
from api.models import Transaction, Wallet, Label
from api.utils.serialize import _serialize
from api.utils.week import get_wom_from_date

@permission_classes([IsAuthenticated])
class create(generics.GenericAPIView):
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
            "week": get_wom_from_date(date_time),
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
        data["wallet"].balance = round(data["wallet"].balance + data["amount"] * (-1 if data["is_expense"] else 1), ndigits =2)
        data["wallet"].save()

        return Response({
            "success": True,
            "trxn": TransactionSerializer(trxn).data
        })


@permission_classes([IsAuthenticated])
class get(generics.GenericAPIView):
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
            "label_search_type_union", "true") == "true"

        # Extract Wallets
        wallet_ids = []
        _wallets = request.GET.get("wallets", "").split(",")
        if len(_wallets) > 0 and _wallets[0] != "":
            wallet_ids = [int(i) for i in _wallets]

        # Extract Search string
        search_str = request.GET.get("search", "")

        # Build the filters
        search_filters_args, search_filters_kwargs = [], {
            "user": request.user
        }

        if len(wallet_ids) != 0:
            search_filters_kwargs["wallet__id__in"] = wallet_ids

        if search_str != "":
            search_filters_args.append(Q(name__icontains=search_str) | Q(description__icontains=search_str))

        if len(label_ids) != 0 and label_search_union:
            search_filters_kwargs["labels__id__in"] = label_ids

        trxns = Transaction.objects
        if len(label_ids) != 0 and not label_search_union:
            for label in label_ids:
                trxns = trxns.filter(labels__id=label)

        trxns = trxns.filter(*search_filters_args, **search_filters_kwargs).distinct().order_by("-date_time")

        try:
            page = Paginator(trxns, request.GET.get("entries_per_page", 15)).get_page(request.GET.get("page", 1))
        except EmptyPage:
            return Response({
            "success": False,
            "message": "Invalid page requested"
        })
        return Response({
            "success": True,
            "page": {
                "total": page.paginator.num_pages,
                "current": page.number
            },
            "trxns": _serialize(page.object_list, TransactionSerializer)
        })

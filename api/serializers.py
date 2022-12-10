from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Wallet, Transaction, Label


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = "__all__"


class WalletSerializerMinimal(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "name"]


class LabelSerializerMinimal(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ["id", "name"]


class TransactionSerializer(serializers.ModelSerializer):
    labels = LabelSerializerMinimal(many=True)
    wallet = WalletSerializerMinimal()

    class Meta:
        model = Transaction
        fields = [
            "name",
            "description",
            "amount",
            "is_expense",
            "labels",
            "wallet",
            "date_time"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "first_name",
                  "last_name", "date_joined"]

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Wallet(models.Model):
    name = models.CharField("Name of the Wallet", null=False, max_length=50)
    description = models.TextField("Description of the Wallet", default="")
    created_on = models.DateTimeField("Created On", auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    balance = models.IntegerField("Current Balance", default=0)

class Label(models.Model):
    name = models.CharField("Name of the Label", null=False, max_length=50)
    description = models.TextField("Description of the Label", default="")
    created_on = models.DateTimeField("Created On", auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    color = models.CharField("Color of the Label (in hex format)", max_length=7)

class Transaction(models.Model):
    name = models.CharField("Name of the Label", null=False, max_length=100)
    description = models.TextField("Description of the Label", default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    amount = models.IntegerField("Transaction Amount", default=0)
    is_expense = models.BooleanField("Is it an expense?", default=True)
    labels = models.ManyToManyField(Label, verbose_name="Labels")
    wallet = models.ForeignKey(Wallet, verbose_name="Wallet Used for Transaction", on_delete=models.CASCADE)

    date_time = models.DateTimeField("Date & Time of Transaction", auto_now_add=True)

    # These will be used to crete data rich statistics for the user
    day = models.IntegerField("Date of the Month")
    week = models.IntegerField("Week of the Month")
    month = models.IntegerField("Month Of the Year")
    year = models.IntegerField("Year of Transaction")
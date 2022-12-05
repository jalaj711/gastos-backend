from django.contrib import admin
from .models import Wallet, Transaction, Label, User

# Register your models here.
admin.register(Wallet, Transaction, Label, User)

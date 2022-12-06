from django.contrib import admin
from .models import Wallet, Transaction, Label

# Register your models here.
admin.site.register([Wallet, Transaction, Label])

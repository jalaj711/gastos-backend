from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = [
    path('login/', csrf_exempt(views.login.as_view()), name='login'),
    path('register/', csrf_exempt(views.register.as_view()), name='register'),
    path('create-trxn/', csrf_exempt(views.create_transaction.as_view()), name='create_trxn'),
    path('create-label/', csrf_exempt(views.create_label.as_view()), name='create_label'),
    path('create-wallet/', csrf_exempt(views.create_wallet.as_view()), name='create_wallet'),
    path('get-trxn/', csrf_exempt(views.get_transactions.as_view()), name='get_trxn'),
    path('get-wallets/', csrf_exempt(views.get_wallets.as_view()), name='get_wallets'),
    path('get-labels/', csrf_exempt(views.get_labels.as_view()), name='get_labels'),
    path('get-label-stats/', csrf_exempt(views.get_label_stats.as_view()), name='get_label_stats'),
    path('get-wallet-stats/', csrf_exempt(views.get_wallet_stats.as_view()), name='get_wallet_stats'),
]

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = [
    path('login/', csrf_exempt(views.login.as_view()), name='login'),
    path('register/', csrf_exempt(views.register.as_view()), name='register'),
    path('create-trxn/', csrf_exempt(views.create_transaction.as_view()), name='create_trxn'),
    path('create-label/', csrf_exempt(views.create_label.as_view()), name='create_label'),
    path('create-wallet/', csrf_exempt(views.create_wallet.as_view()), name='create_wallet'),
]

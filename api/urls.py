from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = [
    path('login/', csrf_exempt(views.login.as_view()), name='login'),
    path('register/', csrf_exempt(views.register.as_view()), name='register'),
]

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

API_BASE = ""

USER_URLS = {
    "get": views.user.login.as_view(),
    "dashboard": views.user.get_user_stats.as_view()
}

TRANSACTION_URLS = {
    "create": views.transaction.create.as_view(),
    "search": views.transaction.get.as_view()
}

LABEL_URLS = {
    "create": views.label.create.as_view(),
    "get": views.label.get.as_view(),
    "stats": views.label.stats.as_view(),
    "search": views.label.get.as_view()
}

WALLET_URLS = {
    "create": views.wallet.create.as_view(),
    "get": views.wallet.get.as_view(),
    "stats": views.wallet.stats.as_view(),
    "search": views.wallet.get.as_view(),
    "update": views.wallet.update.as_view()
}

AUTH_URLS = {
    "login": views.user.login.as_view(),
    "register": views.user.register.as_view(),
    # "SOCIAL": {
    #     "GOOGLE": "/auth/social/google/",
    #     "FACEBOOK": "/auth/social/facebook/"
    # },
    # "LOGIN": "/auth/login/",
    # "LOGOUT": "/auth/logout/",
    # "SIGNUP": "/auth/signup/",
    # "FORGOT_PASSWORD": "/auth/forgot-password/",
}

URLs = {
    "auth": AUTH_URLS,
    "wallet": WALLET_URLS,
    "label": LABEL_URLS,
    "transactions": TRANSACTION_URLS,
    "user": USER_URLS
}

urlpatterns = []

for url_domain in URLs:
    for url in URLs[url_domain]:
        route = url_domain + "/" + url + "/"
        urlpatterns.append(path(
            route,
            csrf_exempt(URLs[url_domain][url]),
            name=route.replace('/', '_')
        ))


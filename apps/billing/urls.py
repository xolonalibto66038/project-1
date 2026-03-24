from django.urls import path

from .views import (
    CreateCheckoutSessionView,
    PaymentSuccessView,
    PricingPageView,
    SelectPaymentMethodView,
    SubscriptionSuccessView,
    UpgradeView,
)
from .webhooks import stripe_webhook

app_name = "billing"

urlpatterns = [
    path("pricing/", PricingPageView.as_view(), name="pricing"),
    path("upgrade/", UpgradeView.as_view(), name="upgrade"),
    path(
        "checkout/<uuid:plan_pk>/", CreateCheckoutSessionView.as_view(), name="checkout"
    ),
    path(
        "select-method/<uuid:plan_pk>/",
        SelectPaymentMethodView.as_view(),
        name="select-method",
    ),
    path(
        "subscription_success/",
        SubscriptionSuccessView.as_view(),
        name="subscription-success",
    ),
    path("payment_success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("webhook/", stripe_webhook, name="webhook"),
]

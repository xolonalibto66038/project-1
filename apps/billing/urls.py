from django.urls import path

from .views import (
    ChargilyFailureView,
    ChargilySuccessView,
    ChargilyWebhookView,
    CheckoutView,
    CreateCheckoutSessionView,
    PaymentCancelView,
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
    path("payment_cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
    path("webhook/", stripe_webhook, name="webhook"),
    path(
        "chargily_checkout/<uuid:plan_pk>/",
        CheckoutView.as_view(),
        name="chargily-checkout",
    ),
    path(
        "chargily/success/",
        ChargilySuccessView.as_view(),
        name="chargily_success",
    ),
    path(
        "chargily/failure/",
        ChargilyFailureView.as_view(),
        name="chargily_failure",
    ),
    path(
        "chargily/webhook/",
        ChargilyWebhookView.as_view(),
    ),
]

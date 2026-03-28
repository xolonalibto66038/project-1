import hashlib
import hmac
import json

import requests
import stripe
from chargily_pay import ChargilyClient
from chargily_pay.entity import Checkout

# from chargily_pay.settings import CHARGILYPAY_PRODUCTION_URL, CHARGILYPAY_SANDBOX_URL
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View
from django.views.generic import TemplateView

from apps.tutoring.models import ZoomSession

from .choices import OfferTier
from .models import Plan, Subscription  # adjust to your actual models
from .selectors import get_pricing_context, get_user_subscription

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class PricingPageView(TemplateView):
    template_name = "apps/billing/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_pricing_context())
        context["user_subscription"] = get_user_subscription(self.request.user)
        return context


class UpgradeView(LoginRequiredMixin, TemplateView):
    """
    Shown to already-paying users who tried to access a higher-tier feature.
    Pre-selects the required tier and carries ?next= for post-payment redirect.
    """

    template_name = "apps/billing/upgrade.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        required_tier = self.request.GET.get("required_tier", OfferTier.PREMIUM)
        next_url = self.request.GET.get("next", "/")

        ctx["required_tier"] = required_tier
        ctx["next_url"] = next_url
        ctx["current_subscription"] = getattr(self.request.user, "subscription", None)

        # Only show plans for the required tier
        ctx["upgrade_plans"] = Plan.objects.filter(
            offer__tier=required_tier,
            is_active=True,
        ).select_related("offer")

        # Human-readable tier label
        ctx["required_tier_label"] = dict(OfferTier.choices).get(
            required_tier, required_tier
        )

        return ctx


class SelectPaymentMethodView(LoginRequiredMixin, TemplateView):
    template_name = "apps/billing/select_payment_method.html"

    def get(self, request, *args, **kwargs):
        plan = get_object_or_404(Plan, pk=kwargs["plan_pk"], is_active=True)
        return self.render_to_response(self.get_context_data(plan=plan))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plan"] = kwargs["plan"]
        return context


class CreateCheckoutSessionView(LoginRequiredMixin, View):

    ALLOWED_METHODS = {
        "card": ["card"],
        "paypal": ["paypal"],
        "google_pay": ["card"],  # Google Pay flows through card in Stripe
    }

    def post(self, request, *args, **kwargs):
        plan = get_object_or_404(Plan, pk=kwargs["plan_pk"], is_active=True)

        user_subscription = get_user_subscription(request.user)

        stripe_customer_id = None

        if user_subscription and user_subscription.stripe_customer_id:
            stripe_customer_id = user_subscription.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=request.user.email, metadata={"user_id": str(request.user.id)}
            )
            stripe_customer_id = customer.id

        if user_subscription and user_subscription.is_active:
            # Allow if the user is upgrading to a different tier
            if user_subscription.plan.offer.tier == plan.offer.tier:
                return JsonResponse(
                    {"error": "You already have an active subscription for this plan."},
                    status=400,
                )

            # # The proper way to it
            # # Upgrade: modify the existing Stripe subscription instead of creating a new one
            # try:
            #     stripe_sub = stripe.Subscription.retrieve(
            #         user_subscription.stripe_subscription_id
            #     )
            #     updated = stripe.Subscription.modify(
            #         user_subscription.stripe_subscription_id,
            #         items=[
            #             {
            #                 "id": stripe_sub["items"]["data"][0]["id"],
            #                 "price": plan.stripe_price_id,
            #             }
            #         ],
            #         proration_behavior="always_invoice",  # charge the diff immediately
            #         metadata={
            #             "user_id": str(request.user.id),
            #             "plan_id": str(plan.id),
            #         },
            #     )

            #     # Update local DB immediately
            #     user_subscription.plan = plan
            #     user_subscription.status = updated.status
            #     user_subscription.save(update_fields=["plan", "status"])

            #     next_url = (
            #         request.POST.get("next")
            #         or request.GET.get("next")
            #         or "/billing/subscription_success/"
            #     )
            #     return JsonResponse({"redirect_url": next_url})

            # except stripe.error.StripeError as e:
            #     return JsonResponse({"error": str(e)}, status=400)

        if not plan.stripe_price_id:
            return JsonResponse(
                {
                    "error": "This plan is not yet available for purchase. Please try again later."
                },
                status=400,
            )

        method_key = request.POST.get("payment_method", "card")
        payment_methods = self.ALLOWED_METHODS.get(method_key, ["card"])

        # # The proper way
        # next_url = (
        #     request.POST.get("next")
        #     or request.GET.get("next")
        #     or "/billing/subscription_success/"
        # )

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=payment_methods,
                mode="subscription",
                # customer_email=request.user.email,
                customer=stripe_customer_id,
                line_items=[
                    {
                        "price": plan.stripe_price_id,
                        "quantity": 1,
                    }
                ],
                metadata={
                    "user_id": str(request.user.id),
                    "plan_id": str(plan.id),
                },
                success_url=request.build_absolute_uri(
                    "/billing/subscription_success/"
                ),
                # # The proper way
                # success_url=request.build_absolute_uri(
                #     f"/billing/subscription_success/?next={next_url}"
                # ),
                cancel_url=request.build_absolute_uri("/billing/pricing/"),
                # # The proper way
                # cancel_url=request.build_absolute_uri(
                #     request.POST.get("next") or "/billing/pricing/"
                # ),
            )
        except stripe.error.StripeError as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse({"checkout_url": session.url})


class SubscriptionSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "apps/billing/subscription_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_subscription"] = get_user_subscription(self.request.user)
        return context


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "apps/billing/payment_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stripe_session_id = self.request.GET.get("session_id")

        if stripe_session_id:
            tutoring_session = (
                ZoomSession.objects.filter(
                    stripe_checkout_session_id=stripe_session_id,
                    student=self.request.user,
                )
                .select_related(
                    "teacher",
                    "teacher__teacher_profile",
                )
                .first()
            )

            context["session"] = tutoring_session

        return context


class PaymentFailureView(LoginRequiredMixin, TemplateView):
    template_name = "apps/billing/payment_failure.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_subscription"] = get_user_subscription(self.request.user)
        return context


class PaymentCancelView(View):
    template_name = "apps/billing/payment_cancel.html"

    def get(self, request):
        return render(request, self.template_name)


def _chargily_client() -> ChargilyClient:
    return ChargilyClient(
        key=settings.CHARGILY_APP_KEY,
        secret=settings.CHARGILY_APP_SECRET,
        # url="https://pay.chargily.net/test/api/v2",
        url="https://pay.chargily.net/test/api/pay-v2",
    )


# ── Checkout dispatcher (POST) ───────────────────────────────────────────────


class CheckoutView(LoginRequiredMixin, View):

    def post(self, request, plan_pk):
        plan = get_object_or_404(Plan, pk=plan_pk, is_active=True)
        method = request.POST.get("payment_method", "")

        if method == "chargily":
            return self._chargily_checkout(request, plan)

        # --- existing Stripe-based methods (card / paypal / google_pay) -----
        # keep your existing Stripe logic here, e.g.:
        # return self._stripe_checkout(request, plan, method)

        return JsonResponse({"error": "Unknown payment method."}, status=400)

    def get(self, request, plan_pk):
        plan = get_object_or_404(Plan, pk=plan_pk, is_active=True)
        return self._chargily_checkout(request, plan, redirect_mode=True)

    # ── Chargily ─────────────────────────────────────────────────────────────
    # def _chargily_checkout(self, request, plan, redirect_mode=False):
    #     client = _chargily_client()
    #     CHARGILY_EUR_TO_DZD_RATE = 145  # approx rate, adjust as needed

    #     amount_dzd = max(round(float(plan.price) * CHARGILY_EUR_TO_DZD_RATE, 2), 10.0)

    #     success_url = (
    #         request.build_absolute_uri(settings.CHARGILY_SUCCESS_URL)
    #         + f"?plan={plan.pk}"
    #     )
    #     failure_url = request.build_absolute_uri(settings.CHARGILY_FAILURE_URL)
    #     webhook_url = request.build_absolute_uri(settings.CHARGILY_WEBHOOK_URL)

    #     checkout = client.create_checkout(
    #         Checkout(
    #             amount=amount_dzd,
    #             currency="dzd",
    #             success_url=success_url,
    #             failure_url=failure_url,
    #             webhook_endpoint=webhook_url,
    #             metadata={
    #                 "user_id": str(request.user.pk),
    #                 "plan_id": str(plan.pk),
    #             },
    #             description=f"{plan.offer.name} — {plan.get_interval_display()}",
    #         )
    #     )

    #     checkout_url = checkout["checkout_url"]

    #     if redirect_mode:
    #         from django.shortcuts import redirect

    #         return redirect(checkout_url)

    #     return JsonResponse({"checkout_url": checkout_url})

    def _chargily_checkout(self, request, plan, redirect_mode=False):
        CHARGILY_EUR_TO_DZD_RATE = 145
        amount_dzd = max(round(float(plan.price) * CHARGILY_EUR_TO_DZD_RATE, 2), 10.0)

        success_url = (
            request.build_absolute_uri(settings.CHARGILY_SUCCESS_URL)
            + f"?plan={plan.pk}"
        )
        failure_url = request.build_absolute_uri(settings.CHARGILY_FAILURE_URL)
        webhook_url = request.build_absolute_uri(settings.CHARGILY_WEBHOOK_URL)

        base_url = (
            "https://pay.chargily.net/test/api/v2"
            if settings.DEBUG
            else "https://pay.chargily.net/api/v2"
        )

        response = requests.post(
            f"{base_url}/checkouts",
            headers={
                "Authorization": f"Bearer {settings.CHARGILY_APP_SECRET}",
                "Content-Type": "application/json",
            },
            json={
                "amount": amount_dzd,
                "currency": "dzd",
                "success_url": success_url,
                "failure_url": failure_url,
                "webhook_endpoint": webhook_url,
                "metadata": {
                    "user_id": str(request.user.pk),
                    "plan_id": str(plan.pk),
                },
                "description": f"{plan.offer.name} — {plan.get_interval_display()}",
            },
        )
        response.raise_for_status()
        checkout_url = response.json()["checkout_url"]

        if redirect_mode:
            from django.shortcuts import redirect

            return redirect(checkout_url)

        return JsonResponse({"checkout_url": checkout_url})


# ── Chargily redirect landing pages ─────────────────────────────────────────


class ChargilySuccessView(LoginRequiredMixin, TemplateView):
    """
    Chargily redirects here after a successful payment.
    Do NOT provision access here — wait for the webhook.
    Just show a friendly "we're processing" message.
    """

    template_name = "apps/billing/chargily_success.html"


class ChargilyFailureView(LoginRequiredMixin, TemplateView):
    template_name = "apps/billing/chargily_failure.html"


# ── Chargily webhook (server-to-server) ─────────────────────────────────────


class ChargilyWebhookView(View):
    """
    Receives POST events from Chargily.
    Verifies the HMAC-SHA256 signature, then provisions the subscription.
    """

    def post(self, request):
        # 1. Verify signature
        signature = request.headers.get("signature", "")
        payload = request.body

        expected = hmac.new(
            settings.CHARGILY_APP_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return HttpResponse(status=403)

        # 2. Parse event
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        # 3. Handle checkout.paid
        if event.get("type") == "checkout.paid":
            self._handle_checkout_paid(event["data"])

        return HttpResponse(status=200)

    def _handle_checkout_paid(self, data):
        metadata = data.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id")

        if not user_id or not plan_id:
            return

        # Provision the subscription — adjust to your models
        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            user = User.objects.get(pk=user_id)
            plan = Plan.objects.get(pk=plan_id, is_active=True)
        except (User.DoesNotExist, Plan.DoesNotExist):
            return

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "plan": plan,
                "status": "active",
                # set your period dates here if needed
            },
        )

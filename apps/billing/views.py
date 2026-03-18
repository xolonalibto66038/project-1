import stripe
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from apps.tutoring.models import TutoringSession

from .models import Plan
from .selectors import get_pricing_context, get_user_subscription

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


class PricingPageView(TemplateView):
    template_name = "apps/billing/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_pricing_context())
        context["user_subscription"] = get_user_subscription(self.request.user)
        return context


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
            return JsonResponse(
                {"error": "You already have an active subscription."}, status=400
            )

        if not plan.stripe_price_id:
            return JsonResponse(
                {
                    "error": "This plan is not yet available for purchase. Please try again later."
                },
                status=400,
            )

        method_key = request.POST.get("payment_method", "card")
        payment_methods = self.ALLOWED_METHODS.get(method_key, ["card"])

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
                cancel_url=request.build_absolute_uri("/billing/pricing/"),
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
                TutoringSession.objects.filter(
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

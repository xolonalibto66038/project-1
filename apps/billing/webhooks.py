import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Plan, Subscription
from apps.accounts.models.custom_user import CustomUser

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    handlers = {
        'checkout.session.completed'   : _handle_checkout_completed,
        'customer.subscription.created': _handle_subscription_created,
        'customer.subscription.updated': _handle_subscription_updated,
        'customer.subscription.deleted': _handle_subscription_deleted,
        'invoice.payment_failed':        _handle_payment_failed,
    }

    handler = handlers.get(event["type"])
    if handler:
        handler(event['data']['object'])

    return HttpResponse(status=200)


def _handle_subscription_created(subscription_obj):
    user_id = subscription_obj['metadata'].get('user_id')
    plan_id = subscription_obj['metadata'].get('plan_id')
    stripe_customer_id = subscription_obj.get("customer")

    if not user_id or not plan_id:
        return

    try:
        user = CustomUser.objects.get(id=user_id)
        plan = Plan.objects.get(id=plan_id)
    except (CustomUser.DoesNotExist, Plan.DoesNotExist):
        return

    Subscription.objects.update_or_create(
        user=user,
        defaults={
            'plan':                    plan,
            'stripe_subscription_id':  subscription_obj['id'],
            'stripe_customer_id': stripe_customer_id,
            'status':                  subscription_obj['status'],
            'current_period_end':      timezone.datetime.fromtimestamp(
                subscription_obj['current_period_end'],
                tz=timezone.utc,
            ),
        },
    )


def _handle_checkout_completed(session):

    if session["mode"] != "subscription":
        return

    user_id = session["metadata"].get("user_id")
    plan_id = session["metadata"].get("plan_id")
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")

    if not user_id or not plan_id or not subscription_id:
        return

    try:
        user = CustomUser.objects.get(id=user_id)
        plan = Plan.objects.get(id=plan_id)
    except (CustomUser.DoesNotExist, Plan.DoesNotExist):
        return
    
    subscription = stripe.Subscription.retrieve(subscription_id)

    current_period_end = None
    if hasattr(subscription, "current_period_end"):
        current_period_end = timezone.datetime.fromtimestamp(
            subscription.current_period_end,
            tz=timezone.utc,
        )

    Subscription.objects.update_or_create(
        user=user,
        defaults={
            "plan": plan,
            "stripe_subscription_id": subscription.id,
            "stripe_customer_id": customer_id,
            "status": subscription.status,
            "current_period_end": current_period_end,
        },
    )

def _handle_subscription_updated(subscription_obj):
    try:
        sub = Subscription.objects.get(
            stripe_subscription_id=subscription_obj['id']
        )
        sub.status               = subscription_obj['status']
        sub.cancel_at_period_end = subscription_obj['cancel_at_period_end']
        sub.current_period_end   = timezone.datetime.fromtimestamp(
            subscription_obj['current_period_end'],
            tz=timezone.utc,
        )
        sub.save()
    except Subscription.DoesNotExist:
        pass


def _handle_subscription_deleted(subscription_obj):
    Subscription.objects.filter(
        stripe_subscription_id=subscription_obj['id']
    ).update(status='canceled')


def _handle_payment_failed(invoice_obj):
    sub_id = invoice_obj.get('subscription')
    if sub_id:
        Subscription.objects.filter(
            stripe_subscription_id=sub_id
        ).update(status='past_due')
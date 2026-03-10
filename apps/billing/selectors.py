# apps/payments/selectors.py

from .choices import PlanInterval
from .models import Offer


def get_pricing_context():
    offers = (
        Offer.objects.filter(is_active=True).prefetch_related("plans").order_by("order")
    )

    intervals = [
        {"value": PlanInterval.MONTHLY, "label": "1 Month"},
        {"value": PlanInterval.BIANNUAL, "label": "6 Months"},
        {"value": PlanInterval.ANNUAL, "label": "12 Months"},
    ]

    matrix = []
    for offer in offers:
        plans_by_interval = {p.interval: p for p in offer.plans.filter(is_active=True)}

        # ── Parse features here, not in template ──
        parsed_features = []
        for f in offer.features:
            if f.startswith("-"):
                parsed_features.append(
                    {
                        "text": f[1:].strip(),
                        "included": False,
                    }
                )
            else:
                parsed_features.append(
                    {
                        "text": f.strip(),
                        "included": True,
                    }
                )

        matrix.append(
            {
                "offer": offer,
                "plans_by_interval": plans_by_interval,
                "features": parsed_features,  # ← parsed, not raw
            }
        )

    return {
        "matrix": matrix,
        "intervals": intervals,
        "default_interval": PlanInterval.MONTHLY,
    }


# def get_pricing_context():
#     """
#     Returns everything the pricing page needs in one call.
#     """
#     offers = (
#         Offer.objects
#         .filter(is_active=True)
#         .prefetch_related('plans')
#         .order_by('order')
#     )

#     intervals = [
#         {'value': PlanInterval.MONTHLY,  'label': '1 Month'},
#         {'value': PlanInterval.BIANNUAL, 'label': '6 Months'},
#         {'value': PlanInterval.ANNUAL,   'label': '12 Months'},
#     ]

#     # Build offer × interval matrix for template
#     matrix = []
#     for offer in offers:
#         plans_by_interval = {
#             p.interval: p
#             for p in offer.plans.filter(is_active=True)
#         }
#         matrix.append({
#             'offer':             offer,
#             'plans_by_interval': plans_by_interval,
#         })

#     return {
#         'matrix':    matrix,
#         'intervals': intervals,
#         'default_interval': PlanInterval.MONTHLY,
#     }


def get_user_subscription(user):
    if not user.is_authenticated:
        return None
    try:
        return user.subscription
    except Exception:
        return None

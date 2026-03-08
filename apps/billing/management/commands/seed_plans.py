from django.core.management.base import BaseCommand
from ...models import Offer, Plan
from ...choices import OfferTier, PlanInterval


OFFERS = [
    {
        'tier':        OfferTier.FREE,
        'name':        'Free',
        'description': 'Get started with the basics.',
        'order':       1,
        'features': [
            'Access to all free resources',
            'Browse courses and exercises',
            'Progress tracking',
            '-Priority support',
            '-Downloadable resources',
            '-Live tutoring',
        ],
        'plans': [],
    },
    {
        'tier':        OfferTier.STANDARD,
        'name':        'Standard',
        'description': 'Everything you need to succeed.',
        'order':       2,
        'features': [
            'Everything in Free',
            'Access to all premium courses',
            'All exercises and solutions',
            'Downloadable resources',
            'Email support',
            '-Live tutoring sessions',
        ],
        'plans': [
            {'interval': PlanInterval.MONTHLY,  'price': '9.99',  'original': None,    'popular': False},
            {'interval': PlanInterval.BIANNUAL, 'price': '49.99', 'original': '59.94', 'popular': True},
            {'interval': PlanInterval.ANNUAL,   'price': '89.99', 'original': '119.88','popular': False},
        ],
    },
    {
        'tier':        OfferTier.PREMIUM,
        'name':        'Premium',
        'description': 'The complete learning experience.',
        'order':       3,
        'features': [
            'Everything in Standard',
            'Live tutoring sessions',
            'Priority support',
            'Early access to new content',
            'Personalised study plan',
            'Offline downloads',
        ],
        'plans': [
            {'interval': PlanInterval.MONTHLY,  'price': '19.99', 'original': None,    'popular': False},
            {'interval': PlanInterval.BIANNUAL, 'price': '99.99', 'original': '119.94','popular': True},
            {'interval': PlanInterval.ANNUAL,   'price': '179.99','original': '239.88','popular': False},
        ],
    },
]


class Command(BaseCommand):
    help = 'Seeds Offer and Plan records.'

    def handle(self, *args, **kwargs):
        for offer_data in OFFERS:
            plans_data = offer_data.pop('plans')
            offer, created = Offer.objects.update_or_create(
                tier=offer_data['tier'],
                defaults=offer_data,
            )
            self.stdout.write(
                f"{'Created' if created else 'Updated'} offer: {offer.name}"
            )

            for p in plans_data:
                plan, _ = Plan.objects.update_or_create(
                    offer=offer,
                    interval=p['interval'],
                    defaults={
                        'price':          p['price'],
                        'original_price': p['original'],
                        'is_popular':     p['popular'],
                    },
                )
                self.stdout.write(f"  → {plan}")
from django.contrib import admin

from .models import Offer, Plan, Subscription

admin.site.register(Plan)
admin.site.register(Offer)
admin.site.register(Subscription)

from django.contrib import admin

from .models import GoogleSession, TutoringSession

admin.site.register(TutoringSession)
admin.site.register(GoogleSession)

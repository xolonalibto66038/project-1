from django.contrib import admin

from .models import GoogleSession, ZoomSession

admin.site.register(ZoomSession)
admin.site.register(GoogleSession)

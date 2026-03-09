from django.urls import path

from ..webhooks import zoom_webhook

urlpatterns = [
    path(
        "zoom/",
        zoom_webhook,
        name="zoom-webhook",
    ),
]

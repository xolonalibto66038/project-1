from django.urls import path

from ..views.resource import ResourceDetailView

app_name = "resource"

urlpatterns = [
    path("<uuid:pk>/", ResourceDetailView.as_view(), name="resource-detail"),
]
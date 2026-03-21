from django.urls import path

from ..views.video import ToggleVideoSeenView

app_name = "video"

urlpatterns = [
    path(
        "<uuid:pk>/toggle-seen/",
        ToggleVideoSeenView.as_view(),
        name="video-toggle-seen",
    ),
]

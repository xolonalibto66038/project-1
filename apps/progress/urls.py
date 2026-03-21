from django.urls import path

from .views import SaveVideoProgressView, ToggleContentCompletedView

app_name = "progress"

urlpatterns = [
    path(
        "toggle/<str:app_label>/<str:model>/<uuid:pk>/",
        ToggleContentCompletedView.as_view(),
        name="toggle-completed",
    ),
    path(
        "videos/<uuid:pk>/progress/",
        SaveVideoProgressView.as_view(),
        name="video-save-progress",
    ),
]

from django.urls import path

from ..views.rating import RateContentView

app_name = "rating"

urlpatterns = [
    path(
        "<str:app_label>/<str:model_name>/<uuid:pk>/",
        RateContentView.as_view(),
        name="rate",
    ),
]

from django.urls import path

from ..views import LevelListView, LevelDetailView

app_name = "level"

urlpatterns = [
    path("", LevelListView.as_view(), name="level-list"),
    # path("create/", LevelCreateView.as_view(), name="level-create"),
    path("<uuid:pk>/", LevelDetailView.as_view(), name="level-detail"),
    # path("<uuid:pk>/update/", LevelUpdateView.as_view(), name="level-update"),
    # path("<uuid:pk>/delete/", LevelDeleteView.as_view(), name="level-delete"),
]

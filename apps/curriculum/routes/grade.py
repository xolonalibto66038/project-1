from django.urls import path

from ..views import GradeDetailView

app_name = "grade"

urlpatterns = [
    # path("", GradeListView.as_view(), name="grade-list"),
    # path("create/", GradeCreateView.as_view(), name="grade-create"),
    path("<uuid:pk>/", GradeDetailView.as_view(), name="grade-detail"),
    # path("<uuid:pk>/update/", GradeUpdateView.as_view(), name="grade-update"),
    # path("<uuid:pk>/delete/", GradeDeleteView.as_view(), name="grade-delete"),
]
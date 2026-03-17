from django.urls import include, path

app_name = "curriculum"

urlpatterns = [
    path("levels/", include("apps.curriculum.routes.level")),
    path("grades/", include("apps.curriculum.routes.grade")),
    path("subjects/", include("apps.curriculum.routes.subject")),
    path("grade_subjects/", include("apps.curriculum.routes.grade_subject")),
]

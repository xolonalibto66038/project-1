from django.urls import include, path

app_name = "curriculum"

urlpatterns = [
    path("level/", include("apps.curriculum.routes.level")),
    path("grade/", include("apps.curriculum.routes.grade")),
    path("subject/", include("apps.curriculum.routes.subject")),
]

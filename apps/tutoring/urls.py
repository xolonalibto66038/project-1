from django.urls import include, path

app_name = "tutoring"

urlpatterns = [
    path("student/", include("apps.tutoring.routes.student")),
    path("teacher/", include("apps.tutoring.routes.teacher")),
    path("webhook/", include("apps.tutoring.routes.webhook")),
]

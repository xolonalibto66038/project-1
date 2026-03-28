from django.urls import include, path

app_name = "tutoring"

urlpatterns = [
    path("student/", include("apps.tutoring.routes.student")),
    path("teacher/", include("apps.tutoring.routes.teacher")),
    path("meet/", include("apps.tutoring.routes.meet")),
    path("zoom/", include("apps.tutoring.routes.zoom")),
    path("webhook/", include("apps.tutoring.routes.webhook")),
]

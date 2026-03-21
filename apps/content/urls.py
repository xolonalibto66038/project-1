from django.urls import include, path

app_name = "content"

urlpatterns = [
    path("courses/", include("apps.content.routes.course")),
    path("resource/", include("apps.content.routes.resource")),
    path("video/", include("apps.content.routes.video")),
]

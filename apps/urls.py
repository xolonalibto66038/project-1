from django.urls import include, path

urlpatterns = [
    path("", include("apps.authentication.urls")),
    path("", include("apps.pages.urls")),
    path("curriculum/", include("apps.curriculum.urls")),
    path("content/", include("apps.content.urls")),
]

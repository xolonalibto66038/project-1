from django.urls import include, path

app_name = "feedback"

urlpatterns = [
    path("bookmarks/", include("apps.feedback.routes.bookmark")),
    path("ratings/", include("apps.feedback.routes.rating")),
]

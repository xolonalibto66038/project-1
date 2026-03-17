from django.urls import include, path

urlpatterns = [
    path("", include("apps.authentication.urls")),
    path("", include("apps.pages.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("curriculum/", include("apps.curriculum.urls")),
    path("content/", include("apps.content.urls")),
    path("billing/", include("apps.billing.urls")),
    path("tutoring/", include("apps.tutoring.urls")),
    path("progress/", include("apps.progress.urls")),
    path("feedback/", include("apps.feedback.urls")),
    path("assessment/", include("apps.assessment.urls")),
    path("recommender/", include("apps.recommender.urls")),
]

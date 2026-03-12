from django.urls import include, path

app_name = "assessment"

urlpatterns = [
    path("questions/", include("apps.assessment.routes.question")),
    path("quizzes/", include("apps.assessment.routes.quiz")),
]

from django.urls import path

from ..views.quiz import (
    QuizAddQuestionView,
    QuizCreateView,
    QuizDeleteView,
    QuizDetailView,
    QuizListView,
    QuizUpdateView,
    StudentTakeQuizView,
)

app_name = "quiz"

urlpatterns = [
    path(
        "quiz/create/",
        QuizCreateView.as_view(),
        name="quiz-create",
    ),
    path(
        "quiz/list/",
        QuizListView.as_view(),
        name="quiz-list",
    ),
    path(
        "quiz/<uuid:pk>/add-question/",
        QuizAddQuestionView.as_view(),
        name="quiz-add-question",
    ),
    path(
        "quiz/<uuid:pk>/quiz_detail",
        QuizDetailView.as_view(),
        name="quiz-detail",
    ),
    path(
        "quizzes/<uuid:pk>/edit/",
        QuizUpdateView.as_view(),
        name="quiz-update",
    ),
    path(
        "quizzes/<uuid:pk>/delete/",
        QuizDeleteView.as_view(),
        name="quiz-delete",
    ),
    path("quiz/<uuid:pk>/take/", StudentTakeQuizView.as_view(), name="quiz-take"),
]

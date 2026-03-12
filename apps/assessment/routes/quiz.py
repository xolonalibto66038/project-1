from django.urls import path

from ..views.quiz import (
    QuizAddQuestionView,
    QuizCreateView,
    QuizDeleteView,
    QuizDetailView,
    QuizListView,
    QuizUpdateView,
    StudentTakeQuizView,
    QuizResultView,
    QuizAttemptsView
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
    path("grade-subject/<uuid:grade_subject_pk>/quiz/<uuid:pk>/take/", StudentTakeQuizView.as_view(), name="quiz-take"),
    path(
        "quizzes/result/<uuid:attempt_id>/",
        QuizResultView.as_view(),
        name="quiz-result",
    ),
    path(
    "quizzes/<uuid:pk>/attempts/",
        QuizAttemptsView.as_view(),
        name="quiz-attempts",
    ),
]

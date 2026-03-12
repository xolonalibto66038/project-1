from django.urls import path

from ..views.question import (
    EssayQuestionCreateView,
    EssayQuestionUpdateView,
    MultipleChoiceQuestionCreateView,
    MultipleChoiceQuestionUpdateView,
    QuestionListView,
    TrueFalseQuestionCreateView,
    TrueFalseQuestionUpdateView,
)

app_name = "question"

urlpatterns = [
    path(
        "essay/create/",
        EssayQuestionCreateView.as_view(),
        name="essay-create",
    ),
    path(
        "essay/<uuid:pk>/edit/",
        EssayQuestionUpdateView.as_view(),
        name="essay-update",
    ),
    path(
        "true-false/create/",
        TrueFalseQuestionCreateView.as_view(),
        name="tf-create",
    ),
    path(
        "true-false/<uuid:pk>/edit/",
        TrueFalseQuestionUpdateView.as_view(),
        name="tf-update",
    ),
    path(
        "mcq/create/",
        MultipleChoiceQuestionCreateView.as_view(),
        name="mcq-create",
    ),
    path(
        "mcq/<uuid:pk>/edit/",
        MultipleChoiceQuestionUpdateView.as_view(),
        name="mcq-update",
    ),
    path(
        "list/",
        QuestionListView.as_view(),
        name="question-list",
    ),
]

# # forms.py
from django import forms
from django.contrib.contenttypes.models import ContentType

from ..models import EssayQuestion, MultipleChoiceQuestion, TrueFalseQuestion

QUESTION_MODELS = {
    "mcq": MultipleChoiceQuestion,
    "essay": EssayQuestion,
    "tf": TrueFalseQuestion,
}


class AddQuestionToQuizForm(forms.Form):
    question_type = forms.ChoiceField(
        choices=[
            ("mcq", "Multiple Choice"),
            ("tf", "True / False"),
            ("essay", "Essay"),
        ],
        # widget=forms.Select(attrs={"class": "form-control"}),
        widget=forms.Select(
            attrs={"class": "form-control", "onchange": "this.form.submit();"}
        ),
    )

    question = forms.ChoiceField(
        label="Select Question",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    points_override = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher", None)
        super().__init__(*args, **kwargs)

        self.teacher = teacher

        # Initially empty
        self.fields["question"].choices = []

        # If POST, load correct queryset
        if "question_type" in self.data and teacher:
            q_type = self.data.get("question_type")
            model = QUESTION_MODELS.get(q_type)

            if model:
                questions = model.objects.filter(created_by=teacher).order_by(
                    "-created_at"
                )

                self.fields["question"].choices = [(q.id, q.title) for q in questions]


# from django import forms
# from django.contrib.contenttypes.models import ContentType

# from ..models import MultipleChoiceQuestion, QuizQuestion


# class AddQuestionToQuizForm(forms.Form):
#     question = forms.ModelChoiceField(
#         queryset=MultipleChoiceQuestion.objects.none(),
#         label="Select Question",
#         widget=forms.Select(attrs={"class": "form-control"}),
#     )

#     points_override = forms.IntegerField(
#         required=False,
#         min_value=1,
#         widget=forms.NumberInput(attrs={"class": "form-control"}),
#         label="Override Points (optional)",
#     )

#     def __init__(self, *args, **kwargs):
#         teacher = kwargs.pop("teacher", None)
#         super().__init__(*args, **kwargs)

#         if teacher:
#             self.fields["question"].queryset = MultipleChoiceQuestion.objects.filter(
#                 created_by=teacher
#             ).order_by("-created_at")

from django import forms
from ..models import EssayQuestion, MultipleChoiceQuestion, TrueFalseQuestion

QUESTION_MODELS = {
    "mcq":   (MultipleChoiceQuestion, "Multiple Choice"),
    "essay": (EssayQuestion,          "Essay"),
    "tf":    (TrueFalseQuestion,      "True / False"),
}


class AddQuestionToQuizForm(forms.Form):

    question = forms.ChoiceField(
        label="Question",
        widget=forms.Select(attrs={"class": "form-control select2"}),
    )

    points_override = forms.IntegerField(
        required=False,
        min_value=1,
        label="Points Override",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop("teacher")
        super().__init__(*args, **kwargs)

        choices = [("", "— Select a question —")]

        for q_type, (model, label) in QUESTION_MODELS.items():
            questions = (
                model.objects
                .filter(created_by=teacher)
                .order_by("-created_at")
            )
            for q in questions:
                # Encode type + id together: "mcq:uuid"
                value = f"{q_type}:{q.id}"
                display = f"{q.title} — {label}"
                choices.append((value, display))

        self.fields["question"].choices = choices

    def clean_question(self):
        value = self.cleaned_data.get("question")
        if not value:
            raise forms.ValidationError("Please select a question.")

        # Validate format
        try:
            q_type, question_id = value.split(":", 1)
        except ValueError:
            raise forms.ValidationError("Invalid question selection.")

        if q_type not in QUESTION_MODELS:
            raise forms.ValidationError("Invalid question type.")

        model, _ = QUESTION_MODELS[q_type]

        try:
            question = model.objects.get(pk=question_id)
        except model.DoesNotExist:
            raise forms.ValidationError("Question not found.")

        # Return a dict so form_valid has everything it needs
        return {
            "q_type":   q_type,
            "question": question,
        }

# from django import forms
# from django.contrib.contenttypes.models import ContentType

# from ..models import EssayQuestion, MultipleChoiceQuestion, TrueFalseQuestion

# QUESTION_MODELS = {
#     "mcq":   MultipleChoiceQuestion,
#     "essay": EssayQuestion,
#     "tf":    TrueFalseQuestion,
# }

# QUESTION_TYPE_CHOICES = [
#     ("essay", "Essay"),
#     ("mcq",   "Multiple Choice"),
#     ("tf",    "True / False"),
# ]


# class AddQuestionToQuizForm(forms.Form):

#     question_type = forms.ChoiceField(
#         choices=QUESTION_TYPE_CHOICES,
#         widget=forms.Select(attrs={
#             "class":    "form-control",
#             "onchange": "this.form.submit();",
#         }),
#     )

#     question = forms.ChoiceField(
#         label="Select Question",
#         widget=forms.Select(attrs={"class": "form-control"}),
#     )

#     points_override = forms.IntegerField(
#         required=False,
#         min_value=1,
#         label="Points Override",
#         widget=forms.NumberInput(attrs={"class": "form-control"}),
#     )

#     def __init__(self, *args, **kwargs):
#         teacher      = kwargs.pop("teacher")
#         initial_type = kwargs.pop("initial_type", "essay")
#         super().__init__(*args, **kwargs)

#         # Resolve active type — POST wins over GET default
#         active_type = self.data.get("question_type", initial_type)

#         # Guard against invalid type
#         if active_type not in QUESTION_MODELS:
#             active_type = "essay"

#         self.fields["question_type"].initial = active_type

#         # Load questions for active type
#         model     = QUESTION_MODELS[active_type]
#         questions = (
#             model.objects
#             .filter(created_by=teacher)
#             .order_by("-created_at")
#         )

#         self.fields["question"].choices = [
#             ("", "— Select a question —"),
#             *[(str(q.id), q.title) for q in questions],
#         ]

#     def clean_question(self):
#         value = self.cleaned_data.get("question")
#         if not value:
#             raise forms.ValidationError("Please select a question.")
#         return value
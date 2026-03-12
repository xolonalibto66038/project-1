from django import forms

from ..models import TrueFalseQuestion


class TrueFalseQuestionForm(forms.ModelForm):
    class Meta:
        model = TrueFalseQuestion
        fields = [
            "title",
            "question_text",
            "points",
            "difficulty_level",
            "tags",
            "correct_answer",
            "explanation",
            "is_active",
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter question title"}
            ),
            "question_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Write the True/False statement...",
                }
            ),
            "points": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "difficulty_level": forms.Select(attrs={"class": "form-control"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-control"}),
            "correct_answer": forms.Select(
                choices=[
                    (True, "True"),
                    (False, "False"),
                ],
                attrs={"class": "form-control"},
            ),
            "explanation": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional explanation shown after submission",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

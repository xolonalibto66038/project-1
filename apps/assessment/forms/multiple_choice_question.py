from django import forms
from django.forms import inlineformset_factory

from ..models import Choice, MultipleChoiceQuestion


class MultipleChoiceQuestionForm(forms.ModelForm):
    class Meta:
        model = MultipleChoiceQuestion
        fields = [
            "title",
            "question_text",
            "points",
            "difficulty_level",
            "tags",
            "allow_multiple",
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
                    "placeholder": "Write the question...",
                }
            ),
            "points": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "difficulty_level": forms.Select(attrs={"class": "form-control"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-control"}),
            "allow_multiple": forms.CheckboxInput(
                attrs={"class": "form-check-input", "id": "id_allow_multiple"}
            ),
            "explanation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ["text", "is_correct", "order"]

        widgets = {
            "text": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Choice text"}
            ),
            "is_correct": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }


ChoiceCreateFormSet = inlineformset_factory(
    MultipleChoiceQuestion,
    Choice,
    form=ChoiceForm,
    extra=2,
    min_num=2,
    validate_min=True,
    can_delete=True,
)


ChoiceFormSet = inlineformset_factory(
    MultipleChoiceQuestion,
    Choice,
    form=ChoiceForm,
    extra=0,
    min_num=2,
    validate_min=True,
    can_delete=True,
)

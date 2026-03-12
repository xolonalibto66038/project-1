from django import forms

from ..models import EssayQuestion


class EssayQuestionForm(forms.ModelForm):
    class Meta:
        model = EssayQuestion
        fields = [
            "title",
            "question_text",
            "points",
            "difficulty_level",
            "tags",
            "min_length",
            "max_length",
            "sample_answer",
            "explanation",
            "is_auto_gradable",
            "keywords",
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
                    "placeholder": "Write the question here...",
                }
            ),
            "points": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "difficulty_level": forms.Select(attrs={"class": "form-control"}),
            "tags": forms.SelectMultiple(attrs={"class": "form-control"}),
            "min_length": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "max_length": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "sample_answer": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "explanation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_auto_gradable": forms.CheckboxInput(
                attrs={"class": "form-check-input", "id": "id_is_auto_gradable"}
            ),
            "keywords": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "keyword1, keyword2, keyword3",
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_length = cleaned_data.get("min_length")
        max_length = cleaned_data.get("max_length")

        if min_length and max_length and min_length > max_length:
            self.add_error("min_length", "Minimum length cannot exceed maximum length.")

        if cleaned_data.get("is_auto_gradable") and not cleaned_data.get("keywords"):
            self.add_error(
                "keywords", "Keywords are required when auto-grading is enabled."
            )

        return cleaned_data

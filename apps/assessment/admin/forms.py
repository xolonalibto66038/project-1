from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm, Textarea
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import Answer, Attempt, EssayQuestion


class TextQuestionAdminForm(ModelForm):
    """Custom form for TextQuestion admin with enhanced validation"""

    class Meta:
        model = EssayQuestion
        fields = "__all__"
        widgets = {
            "question_text": Textarea(attrs={"rows": 4, "cols": 80}),
            "sample_answer": Textarea(attrs={"rows": 6, "cols": 80}),
            "keywords": Textarea(
                attrs={
                    "rows": 3,
                    "cols": 80,
                    "placeholder": "Enter keywords separated by commas (e.g., algorithm, data structure, python)",
                }
            ),
            "explanation": Textarea(attrs={"rows": 4, "cols": 80}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_length = cleaned_data.get("min_length")
        max_length = cleaned_data.get("max_length")
        is_auto_gradable = cleaned_data.get("is_auto_gradable")
        keywords = cleaned_data.get("keywords")

        # Validate length constraints
        if min_length and max_length:
            if min_length > max_length:
                raise ValidationError(
                    "Minimum length cannot be greater than maximum length."
                )

            if min_length < 1:
                raise ValidationError("Minimum length must be at least 1 character.")

        # Validate auto-grading requirements
        if is_auto_gradable and not keywords:
            raise ValidationError("Keywords are required when auto-grading is enabled.")

        return cleaned_data


class AnswerAdminForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = [
            "question_content_type",
            "question_object_id",
            "answer_text",
            "is_correct",
            # "question",
            "answer_text",
            "answer_boolean",
        ]

    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get("question_content_type")
        object_id = cleaned_data.get("question_object_id")

        if not content_type or not object_id:
            raise forms.ValidationError(_("You must select a question."))

        return cleaned_data


class AttemptForm(forms.ModelForm):
    submitted_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )

    started_at = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )

    class Meta:
        model = Attempt
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.fields["started_at"].initial = timezone.now().strftime("%Y-%m-%dT%H:%M")
            self.fields["started_at"].help_text = _(
                "Automatically set to current time if left blank."
            )

    def clean(self):
        cleaned_data = super().clean()
        started_at   = cleaned_data.get("started_at")
        submitted_at = cleaned_data.get("submitted_at")

        if not started_at: 
            cleaned_data["started_at"] = timezone.now()
            started_at = cleaned_data["started_at"]

        if started_at and submitted_at and submitted_at < started_at:
            raise ValidationError(
                _("Submission time cannot be before start time.")
            )

        return cleaned_data
    
    # class Meta:
    #     model = Attempt
    #     fields = "__all__"
    #     widgets = {
    #         "started_at": forms.DateTimeInput(
    #             attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
    #         ),
    #         "submitted_at": forms.DateTimeInput(
    #             attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
    #         ),
    #     }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     # Set default for started_at if creating new attempt
    #     if not self.instance.pk and "started_at" in self.fields:
    #         self.fields["started_at"].initial = timezone.now()
    #         self.fields["started_at"].help_text = (
    #             "Automatically set to current time if left blank"
    #         )

    # def clean(self):
    #     cleaned_data = super().clean()
    #     started_at = cleaned_data.get("started_at")
    #     submitted_at = cleaned_data.get("submitted_at")

    #     # Auto-set started_at if not provided
    #     if not started_at:
    #         cleaned_data["started_at"] = timezone.now()
    #         started_at = cleaned_data["started_at"]

    #     # Validate time relationship
    #     if started_at and submitted_at and submitted_at < started_at:
    #         raise ValidationError("Submission time cannot be before start time")

    #     return cleaned_data

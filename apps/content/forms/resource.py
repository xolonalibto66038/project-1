# apps/content/forms/resource.py

from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.content.choices import ResourceType
from apps.content.models import Course, Resource
from apps.curriculum.models import GradeSubject


class ResourceCreateForm(forms.ModelForm):

    # Metadata fields
    total_marks = forms.IntegerField(
        required=False,
        min_value=0,
        label=_("Total Marks"),
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )
    duration_minutes = forms.IntegerField(
        required=False,
        min_value=0,
        label=_("Duration (minutes)"),
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )
    coefficient = forms.IntegerField(
        required=False,
        min_value=1,
        label=_("Coefficient"),
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )
    due_days = forms.IntegerField(
        required=False,
        min_value=1,
        label=_("Due in (days)"),
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )

    class Meta:
        model = Resource
        fields = [
            "course",
            "grade_subject",
            "title",
            "resource_type",
            "difficulty",
            "term",
            "file",
            "solution_file",
            "has_solution",
            "is_free",
        ]
        widgets = {
            "course": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "grade_subject": forms.Select(
                attrs={"class": "form-control form-control-sm"}
            ),
            "title": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
            "resource_type": forms.Select(
                attrs={
                    "class": "form-control form-control-sm",
                    "id": "id_resource_type",
                }
            ),
            "difficulty": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "term": forms.Select(attrs={"class": "form-control form-control-sm"}),
            "file": forms.ClearableFileInput(attrs={"class": "custom-file-input"}),
            "solution_file": forms.ClearableFileInput(
                attrs={"class": "custom-file-input"}
            ),
            "has_solution": forms.CheckboxInput(
                attrs={"class": "custom-control-input"}
            ),
            "is_free": forms.CheckboxInput(attrs={"class": "custom-control-input"}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher

        if teacher:
            profile = getattr(teacher, "teacher_profile", None)

            if profile and profile.level and profile.subject:
                # Scope courses to the teacher's level + subject
                # Course → Chapter → GradeSubject → Subject/Grade → Level
                self.fields["course"].queryset = (
                    Course.objects.filter(
                        # Course via chapter
                        models.Q(
                            chapter__grade_subject__subject=profile.subject,
                            chapter__grade_subject__grade__level=profile.level,
                        )
                        # Course directly on grade_subject
                        | models.Q(
                            grade_subject__subject=profile.subject,
                            grade_subject__grade__level=profile.level,
                        )
                    )
                    .select_related(
                        "chapter__grade_subject__grade",
                        "chapter__grade_subject__subject",
                        "grade_subject__grade",
                        "grade_subject__subject",
                    )
                    .order_by("title")
                )

                # Scope grade_subject to teacher's level + subject
                self.fields["grade_subject"].queryset = GradeSubject.objects.filter(
                    subject=profile.subject,
                    grade__level=profile.level,
                ).select_related("grade", "subject")
            else:
                self.fields["course"].queryset = Course.objects.none()
                self.fields["grade_subject"].queryset = GradeSubject.objects.none()

        self.fields["course"].required = False
        self.fields["course"].empty_label = _("— Select a course —")
        self.fields["grade_subject"].required = False
        self.fields["grade_subject"].empty_label = _("— Select a grade/subject —")
        self.fields["term"].required = False

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        grade_subject = cleaned_data.get("grade_subject")

        if not course and not grade_subject:
            raise forms.ValidationError(
                _("Please select either a Course or a Grade/Subject.")
            )
        if course and grade_subject:
            raise forms.ValidationError(
                _(
                    "A resource can only belong to a Course or a Grade/Subject, not both."
                )
            )

        if cleaned_data.get("solution_file") and not cleaned_data.get("has_solution"):
            self.add_error(
                "has_solution",
                _("Check 'Has Solution' when attaching a solution file."),
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        resource_type = instance.resource_type
        metadata = {}

        if resource_type in (
            ResourceType.EXERCISE,
            ResourceType.TEST,
            ResourceType.EXAM,
        ):
            if self.cleaned_data.get("total_marks") is not None:
                metadata["total_marks"] = self.cleaned_data["total_marks"]
        if resource_type in (ResourceType.TEST, ResourceType.EXAM):
            if self.cleaned_data.get("duration_minutes") is not None:
                metadata["duration_minutes"] = self.cleaned_data["duration_minutes"]
        if resource_type == ResourceType.EXAM:
            if self.cleaned_data.get("coefficient") is not None:
                metadata["coefficient"] = self.cleaned_data["coefficient"]
        if resource_type == ResourceType.HOMEWORK:
            if self.cleaned_data.get("due_days") is not None:
                metadata["due_days"] = self.cleaned_data["due_days"]

        instance.metadata = metadata

        if commit:
            instance.save()
        return instance


class ResourceEditForm(ResourceCreateForm):
    """
    Identical to ResourceCreateForm but used for updates.
    Pre-populates metadata fields from the instance's JSONField.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if instance:
            # Unpack metadata JSONField back into form fields
            self.fields["total_marks"].initial = instance.total_marks
            self.fields["duration_minutes"].initial = instance.duration_minutes
            self.fields["coefficient"].initial = instance.coefficient
            self.fields["due_days"].initial = instance.due_days

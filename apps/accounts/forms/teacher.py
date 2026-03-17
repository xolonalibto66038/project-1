# apps/accounts/forms/teacher.py

from django import forms

from apps.accounts.models import TeacherProfile
from apps.curriculum.models import Subject


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ["level", "subject", "bio", "hour_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

        profile = self.instance

        # 🔒 Lock fields if verified
        if profile and profile.is_verified_teacher:
            self.fields["level"].disabled = True
            self.fields["subject"].disabled = True

        # Optional: filter subjects based on level
        if self.instance and self.instance.level:
            self.fields["subject"].queryset = Subject.objects.filter(
                level=self.instance.level
            )
        else:
            self.fields["subject"].queryset = Subject.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        if self.instance.is_verified_teacher:
            # 🚫 Prevent changes even if user hacks the request
            cleaned_data["level"] = self.instance.level
            cleaned_data["subject"] = self.instance.subject

        return cleaned_data

    def clean_hour_price(self):
        value = self.cleaned_data["hour_price"]
        if value < 0:
            raise forms.ValidationError("Price cannot be negative")
        return value

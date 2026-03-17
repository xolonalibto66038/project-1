# apps/accounts/forms/student.py

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import StudentProfile


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["grade", "specialty", "bio"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap class to all fields
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    def clean(self):
        cleaned_data = super().clean()

        grade = cleaned_data.get("grade")
        specialty = cleaned_data.get("specialty")

        if grade and specialty and specialty.grade != grade:
            # self.add_error(
            #     "specialty",
            #     "The selected specialty does not belong to the selected grade.",
            # )
            raise forms.ValidationError(
                _("The selected specialty does not belong to the selected grade.")
            )

        return cleaned_data

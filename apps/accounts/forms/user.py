# apps/accounts/forms/user.py

from django import forms

from apps.accounts.models import CustomUser


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "wilaya",
            "phone",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add Bootstrap class to all fields
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

        self.fields["date_of_birth"].widget = forms.DateInput(
            attrs={"class": "form-control", "type": "date"},
            format="%Y-%m-%d",
        )
        self.fields["date_of_birth"].input_formats = ["%Y-%m-%d"]

from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "inputName",
                "placeholder": "Your full name",
            }
        ),
    )
    email = forms.EmailField(
        label="E-Mail",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "id": "inputEmail",
                "placeholder": "Your email address",
            }
        ),
    )
    subject = forms.CharField(
        max_length=150,
        label="Subject",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "inputSubject",
                "placeholder": "Subject",
            }
        ),
    )
    message = forms.CharField(
        label="Message",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "id": "inputMessage",
                "rows": 4,
                "placeholder": "Your message here...",
            }
        ),
    )

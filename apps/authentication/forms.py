# apps/authentication/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _

from allauth.account.forms import SignupForm, LoginForm, ResetPasswordForm, ChangePasswordForm

from apps.accounts.choices import UserRole
from apps.curriculum.models import Level, Grade, Specialty, Subject

class CustomSignupForm(SignupForm):
    """
    Extends allauth SignupForm with:
    - first_name, last_name
    - role selection (Student / Teacher)
    """

    first_name = forms.CharField(
        max_length=100,
        label=_('First Name'),
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': _('First Name'),
        }),
    )
    last_name = forms.CharField(
        max_length=100,
        label=_('Last Name'),
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': _('Last Name'),
        }),
    )
    role = forms.ChoiceField(
        choices=UserRole.choices,
        label=_('I am a'),
        widget=forms.RadioSelect(attrs={'class': 'role-selector'}),
    )

    # ── Email field override for Bootstrap styling ──
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Email Address'),
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Password'),
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': _('Confirm Password'),
        })

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.role       = self.cleaned_data['role']
        user.save()
        return user


class CustomLoginForm(LoginForm):
    """Bootstrap-styled login form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': _('Email Address'),
        })
        self.fields['password'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': _('Password'),
        })
        if 'remember' in self.fields:
            self.fields['remember'].widget.attrs.update({
                'class': 'form-check-input',
            })


class CustomResetPasswordForm(ResetPasswordForm):
    """Bootstrap-styled password reset form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': _('Email Address'),
        })


class CustomChangePasswordForm(ChangePasswordForm):
    """Bootstrap-styled password change form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class StudentOnboardingForm(forms.Form):
    """Step 2 for students — pick grade and specialty."""

    grade = forms.ModelChoiceField(
        queryset=Grade.objects.select_related('level').order_by('level__order', 'order'),
        label=_('Grade'),
        empty_label=_('Select your grade'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_grade'}),
    )
    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.none(),  # populated dynamically
        label=_('Specialty'),
        required=False,
        empty_label=_('Select your specialty (if applicable)'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_specialty'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # populate specialty based on submitted grade
        if 'grade' in self.data:
            try:
                grade_id = self.data.get('grade')
                self.fields['specialty'].queryset = Specialty.objects.filter(
                    grade_id=grade_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.initial.get('grade'):
            self.fields['specialty'].queryset = Specialty.objects.filter(
                grade=self.initial['grade']
            ).order_by('name')

    def clean(self):
        cleaned = super().clean()
        grade     = cleaned.get('grade')
        specialty = cleaned.get('specialty')

        if grade:
            has_specialties = grade.specialties.exists()
            if has_specialties and not specialty:
                raise forms.ValidationError(
                    _('Please select a specialty for your grade.')
                )
            if not has_specialties and specialty:
                raise forms.ValidationError(
                    _('This grade has no specialties.')
                )
        return cleaned


class TeacherOnboardingForm(forms.Form):
    """Step 2 for teachers — pick level and subject."""

    level = forms.ModelChoiceField(
        queryset=Level.objects.order_by('order'),
        label=_('Level'),
        empty_label=_('Select your level'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_level'}),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),  # populated dynamically
        label=_('Subject'),
        empty_label=_('Select your subject'),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_subject'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'level' in self.data:
            try:
                level_id = self.data.get('level')
                self.fields['subject'].queryset = Subject.objects.filter(
                    level_id=level_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.initial.get('level'):
            self.fields['subject'].queryset = Subject.objects.filter(
                level=self.initial['level']
            ).order_by('name')

    def clean(self):
        cleaned  = super().clean()
        level    = cleaned.get('level')
        subject  = cleaned.get('subject')

        if level and subject:
            if subject.level != level:
                raise forms.ValidationError(
                    _('The selected subject does not belong to this level.')
                )
        return cleaned
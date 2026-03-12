from django import forms
from django.core.exceptions import ValidationError

from ..models import Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = [
            "title",
            "description",
            "instructions",
            "time_limit",
            "max_attempts",
            "passing_score",
            "is_published",
            "start_date",
            "end_date",
            "randomize_questions",
            "show_results_immediately",
            "allow_review",
            "grade_subject",  # NEW
            "course",  # NEW
        ]

        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Enter Quiz title"}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "instructions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "time_limit": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "timelimit"}
            ),
            "max_attempts": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Max attempts"}
            ),
            "passing_score": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Passing Score"}
            ),
            "start_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "end_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "grade_subject": forms.Select(attrs={"class": "form-control"}),
            "course": forms.Select(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        grade_subject = cleaned_data.get("grade_subject")
        course = cleaned_data.get("course")

        # Validate dates
        if start and end and end <= start:
            raise ValidationError("End date must be after start date.")

        # Validate only one parent is set
        # if (grade_subject and course) or (not grade_subject and not course):
        #     raise ValidationError(
        #         "Quiz must be linked to either a Subject or a Course, not both."
        #     )
        
        # Only reject if BOTH are set — having neither is now fine
        if grade_subject and course:
            raise ValidationError("Quiz cannot be linked to both a Subject and a Course.")


        return cleaned_data


# class QuizForm(forms.ModelForm):
#     class Meta:
#         model = Quiz
#         fields = [
#             "title",
#             "description",
#             "instructions",
#             "time_limit",
#             "max_attempts",
#             "passing_score",
#             "is_published",
#             "start_date",
#             "end_date",
#             "randomize_questions",
#             "show_results_immediately",
#             "allow_review",
#         ]

#         widgets = {
#             "title": forms.TextInput(
#                 attrs={"class": "form-control", "placeholder": "Enter Quiz title"}
#             ),
#             "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
#             "instructions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
#             "time_limit": forms.TextInput(
#                 attrs={"class": "form-control", "placeholder": "timelimit"}
#             ),
#             "max_attempts": forms.NumberInput(
#                 attrs={"class": "form-control", "placeholder": "Max attempts"}
#             ),
#             "passing_score": forms.NumberInput(
#                 attrs={"class": "form-control", "placeholder": "Passing Score"}
#             ),
#             # "is_published": forms.BooleanField(
#             #     attrs={"class": "form-control", "placeholder": "Publish it"}
#             # ),
#             "start_date": forms.DateTimeInput(
#                 attrs={"class": "form-control", "type": "datetime-local"}
#             ),
#             "end_date": forms.DateTimeInput(
#                 attrs={"class": "form-control", "type": "datetime-local"}
#             ),
#             # "randomize_questions"
#             # "show_results_immediately",
#             # "allow_review",
#         }

#     def clean(self):
#         cleaned_data = super().clean()
#         start = cleaned_data.get("start_date")
#         end = cleaned_data.get("end_date")

#         if start and end and end <= start:
#             raise forms.ValidationError("End date must be after start date.")

#         return cleaned_data

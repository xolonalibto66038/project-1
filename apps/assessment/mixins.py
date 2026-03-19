from apps.content.models import Course
from apps.curriculum.models import GradeSubject


class QuizFormMixin:
    """Scopes grade_subject and course dropdowns to the current teacher."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        teacher_profile = self.request.user.teacher_profile

        if not teacher_profile.subject or not teacher_profile.level:
            form.fields["grade_subject"].queryset = GradeSubject.objects.none()
            form.fields["course"].queryset = Course.objects.none()
            return form

        form.fields["grade_subject"].queryset = (
            GradeSubject.objects.filter(
                subject=teacher_profile.subject,
                grade__level=teacher_profile.level,
            )
            .select_related("grade", "subject", "specialty")
            .only(
                "id",
                "grade__short_name",
                "subject__short_name",
                "specialty__short_name",
            )
        )
        form.fields["course"].queryset = (
            Course.objects.filter(
                grade_subject__subject=teacher_profile.subject,
                grade_subject__grade__level=teacher_profile.level,
            )
            .select_related("grade_subject__grade", "grade_subject__subject")
            .only("id", "title", "grade_subject_id")
        )
        return form

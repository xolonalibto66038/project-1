import logging

from django.urls import reverse
from django.views.generic import DetailView

from ..mixins import GradeLoggingMixin
from ..models import Grade, Specialty
from ..services import build_enriched_grade_subjects

logger = logging.getLogger(__name__)


class GradeDetailView(GradeLoggingMixin, DetailView):
    model = Grade
    template_name = "apps/curriculum/grades/detail.html"
    context_object_name = "grade"

    def get_queryset(self):
        return Grade.objects.select_related("level").all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grade = self.object
        user = self.request.user
        specialty = self._resolve_specialty(user, grade)
        context["enriched_subjects"] = build_enriched_grade_subjects(
            grade=grade,
            user=user,
            specialty=specialty,
        )
        context["specialty"] = specialty
        context["crumbs"] = [
            {"label": "Home", "url": reverse("pages:landing"), "icon": "fas fa-home"},
            {"label": "Levels", "url": reverse("curriculum:level:level-list")},
            {
                "label": grade.level.get_name_display(),
                "url": reverse(
                    "curriculum:level:level-detail", kwargs={"pk": grade.level.pk}
                ),
            },
            {
                "label": f"{grade.short_name}{' - ' + specialty.short_name if specialty else ''}",
                "url": None,
            },
        ]
        return context

    def _resolve_specialty(self, user, grade):
        """
        Priority:
        1. Authenticated student's profile specialty (if matches this grade)
        2. ?specialty=<pk> query param (guest / teacher browsing)
        3. None
        """
        # 1. Student profile
        if user.is_authenticated and getattr(user, "is_student", False):
            try:
                sp = user.student_profile.specialty
                if sp and sp.grade_id == grade.pk:
                    return sp
            except Exception:
                pass

        # 2. Query param fallback
        specialty_pk = self.request.GET.get("specialty")
        if specialty_pk:
            return Specialty.objects.filter(
                pk=specialty_pk,
                grade=grade,
            ).first()

        return None

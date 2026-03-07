import logging

from django.views.generic import DetailView

from ..mixins import GradeLoggingMixin
from ..models import Grade
from ..services import build_enriched_subjects

logger = logging.getLogger(__name__)

class GradeDetailView(GradeLoggingMixin, DetailView):
    model               = Grade
    template_name       = 'apps/curriculum/grades/detail.html'
    context_object_name = 'grade'

    def get_queryset(self):
        return (
            Grade.objects
            .select_related('level')
            .all()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grade   = self.object

        context['enriched_subjects'] = build_enriched_subjects(
            grade=grade,
            user=self.request.user,
        )

        return context

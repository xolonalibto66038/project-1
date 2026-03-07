from django.http import Http404
from django.shortcuts import get_object_or_404


VALID_QUARTERS = ('q1', 'q2', 'q3')


class SubjectQuarterMixin:
    """
    Resolves `subject` and `quarter` from URL kwargs.
    Validates quarter. Raises Http404 on invalid input.
    Injects both into context automatically.
    """

    def dispatch(self, request, *args, **kwargs):
        from ..models import Subject

        self.subject = get_object_or_404(
            Subject.objects.select_related('level').only(
                'id', 'name', 'short_name', 'icon', 'level__id', 'level__name',
            ),
            pk=kwargs['pk'],
        )

        quarter = kwargs.get('quarter', '').lower()
        if quarter not in VALID_QUARTERS:
            raise Http404(
                f"Invalid quarter '{quarter}'. Must be one of {VALID_QUARTERS}"
            )
        self.quarter = quarter

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subject'] = self.subject
        context['quarter'] = self.quarter
        context['level']   = self.subject.level
        return context
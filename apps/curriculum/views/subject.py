from django.views.generic import DetailView, ListView
from django.utils.translation import gettext_lazy as _

from ..models import Subject
from ..services import get_subject_detail
from ..mixins import GradeLoggingMixin, SubjectQuarterMixin
from ..services.subject import build_courses_page

# Term → quarter slug mapping (Term choices: first/second/third)
_TERM_TO_QUARTER = {
    'first':  'q1',
    'second': 'q2',
    'third':  'q3',
}

# Quarter slug → Term value
_QUARTER_TO_TERM = {v: k for k, v in _TERM_TO_QUARTER.items()}


def _current_quarter_from_request(request):
    """
    Reads ?quarter=q1/q2/q3 from GET params.
    Falls back to q1.
    """
    q = request.GET.get('quarter', 'q1')
    return q if q in ('q1', 'q2', 'q3') else 'q1'


class SubjectDetailView(GradeLoggingMixin, DetailView):
    model               = Subject
    template_name       = 'apps/curriculum/subjects/detail.html'
    context_object_name = 'subject'
    pk_url_kwarg        = 'pk'

    def get_queryset(self):
        return Subject.objects.select_related('level')

    def get_context_data(self, **kwargs):
        context         = super().get_context_data(**kwargs)
        subject         = self.object
        current_quarter = _current_quarter_from_request(self.request)

        stats = get_subject_detail(
            subject=subject,
            user=self.request.user,
        )

        context.update(stats)
        context.update({
            'quarters': [
                ('q1', _('1st Term')),
                ('q2', _('2nd Term')),
                ('q3', _('3rd Term')),
            ],
            'current_quarter': current_quarter,
            'level':           subject.level,
        })

        return context


class SubjectCoursesByQuarterView(SubjectQuarterMixin, ListView):
    template_name       = 'apps/curriculum/subjects/courses_by_quarter.html'
    context_object_name = 'courses'
    paginate_by         = 20

    # ListView.get_queryset is bypassed — we build the list ourselves
    # and hand it back as a plain Python list for the paginator.
    def get_queryset(self):
        return build_courses_page(
            subject=self.subject,
            quarter=self.quarter,
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # subject/quarter/level already injected by SubjectQuarterMixin
        context['quarter_display'] = {
            'q1': '1st Term',
            'q2': '2nd Term',
            'q3': '3rd Term',
        }.get(self.quarter, self.quarter.upper())

        context['is_student'] = (
            self.request.user.is_authenticated
            and getattr(self.request.user, 'is_student', False)
        )

        # preserve GET params for pagination links (strip 'page')
        qp = self.request.GET.copy()
        qp.pop('page', None)
        context['querystring'] = qp.urlencode()

        return context
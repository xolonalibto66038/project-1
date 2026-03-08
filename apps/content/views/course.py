import logging

from django.db import transaction
from django.views.generic import DetailView
from django.core.paginator import Paginator
from django.views.generic import ListView

from ..choices import DifficultyLevel
from ..mixins.course import CourseMixin
from ..selectors import get_course_exercises
from ..models import Course
from ..selectors import (
    get_course_by_pk,
    get_course_progress,
    resolve_course_breadcrumb,
)

from ..services import record_course_visit

logger = logging.getLogger(__name__)


class CourseDetailView(DetailView):
    model               = Course
    template_name       = 'apps/content/courses/detail.html'
    context_object_name = 'course'
    pk_url_kwarg        = 'pk'

    def get_object(self, queryset=None):
        # Use our annotated selector instead of the default queryset
        return get_course_by_pk(self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Record visit for students
        if (
            request.user.is_authenticated
            and getattr(request.user, 'is_student', False)
        ):
            with transaction.atomic():
                record_course_visit(request.user, self.object)

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context   = super().get_context_data(**kwargs)
        course    = self.object
        user      = self.request.user
        crumbs    = resolve_course_breadcrumb(course)

        context['active_tab']  = 'details'
        context['term_display'] = course.get_term_display()
        context['breadcrumb']  = crumbs
        context['level']       = crumbs['level']
        context['grade']       = crumbs['grade']
        context['subject']     = crumbs['subject']
        context['chapter']     = crumbs['chapter']

        # Progress (students only)
        context['progress'] = None
        if user.is_authenticated and getattr(user, 'is_student', False):
            context['progress'] = get_course_progress(user, course)

        return context
    

class CourseExercisesView(CourseMixin, ListView):
    template_name       = 'apps/content/courses/course_exercises.html'
    context_object_name = 'exercises'
    paginate_by         = 6

    def get_queryset(self):
        return get_course_exercises(
            course=self.course,
            filters=self.request.GET,
            user=self.request.user,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # preserve GET params for pagination links
        qp = self.request.GET.copy()
        qp.pop('page', None)

        context.update({
            'active_tab':          'exercises',
            'difficulty_choices':  DifficultyLevel.choices,
            'has_solution_choices': [
                ('',  '— All —'),
                ('1', 'With Solution'),
                ('0', 'Without Solution'),
            ],
            'querystring': qp.urlencode(),
            # active filter values — re-populate form fields
            'filter_q':            self.request.GET.get('q', ''),
            'filter_difficulty':   self.request.GET.get('difficulty', ''),
            'filter_has_solution': self.request.GET.get('has_solution', ''),
            'filter_completed':    self.request.GET.get('completed', ''),
        })

        return context
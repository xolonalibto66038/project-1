import logging

from django.shortcuts import get_object_or_404

from ..models import Course
from ..selectors import get_course_by_pk

logger = logging.getLogger(__name__)


class CourseMixin:
    """
    Resolves `course` from URL kwarg `pk`.
    Injects course + breadcrumb context into every subclass view.
    Logs access.
    """
    def get_course(self):
        if not hasattr(self, '_course'):
            self._course = get_course_by_pk(self.kwargs['pk'])
        return self._course

    @property
    def course(self):
        return self.get_course()

    def get_object(self, queryset=None):
        # Return the annotated course as the view's object
        return self.get_course()

    # def dispatch(self, request, *args, **kwargs):
    #     self.course = get_object_or_404(
    #         Course.objects.select_related(
    #             'chapter',
    #             'chapter__grade_subject__grade__level',
    #             'chapter__grade_subject__subject',
    #             'grade_subject__grade__level',
    #             'grade_subject__subject',
    #         ),
    #         pk=kwargs['pk'],
    #         is_active=True,
    #     )

    #     return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        gs    = self.course.effective_grade_subject
        course  = self.course
        grade = gs.grade if gs else None
        level = grade.level if grade else None

        context['course']    = self.course
        context['grade']     = grade
        context['level']     = level
        context['subject']   = gs.subject if gs else None
        context['is_student'] = (
            self.request.user.is_authenticated
            and getattr(self.request.user, 'is_student', False)
        )
        context['resource_tabs'] = [
            ('lessons',   'Lessons',   'fas fa-chalkboard-teacher', course.lessons_count),
            ('summaries', 'Summaries', 'fas fa-align-left',         course.summaries_count),
            ('homeworks', 'Homeworks', 'fas fa-pencil-ruler',       course.homeworks_count),
            ('exercises', 'Exercises', 'fas fa-pencil-alt',         course.exercises_count),
            ('notes',     'Notes',     'fas fa-sticky-note',        course.notes_count),
            ('series',    'Series',    'fas fa-layer-group',        course.series_count),
        ]

        return context
import logging

from django.shortcuts import get_object_or_404

from ..models import Course

logger = logging.getLogger(__name__)


class CourseMixin:
    """
    Resolves `course` from URL kwarg `pk`.
    Injects course + breadcrumb context into every subclass view.
    Logs access.
    """

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(
            Course.objects.select_related(
                'chapter',
                'chapter__grade_subject__grade__level',
                'chapter__grade_subject__subject',
                'grade_subject__grade__level',
                'grade_subject__subject',
            ),
            pk=kwargs['pk'],
            is_active=True,
        )

        logger.info(
            f'{self.__class__.__name__} accessed',
            extra={
                'user_id':   request.user.id if request.user.is_authenticated else None,
                'course_pk': str(self.course.pk),
            },
        )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        gs    = self.course.effective_grade_subject
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

        return context
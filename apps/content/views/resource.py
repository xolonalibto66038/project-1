import logging

from django.http import Http404, FileResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.progress.models import ContentProgress
from apps.content.choices import ResourceType
from apps.content.models.resource import Resource
from apps.content.selectors import (
    get_or_create_resource_progress,
    get_resource_for_detail,
    get_resource_user_rating,
)

logger = logging.getLogger(__name__)


class ResourceDetailView(DetailView):
    """
    Generic resource detail view.
    Works for any ResourceType — template switches on resource.resource_type.
    Currently wired for EXERCISE; extend template for other types.
    """

    model               = Resource
    context_object_name = 'resource'
    pk_url_kwarg        = 'pk'

    def get_template_names(self):
        """
        Route to type-specific template.
        Fallback: content/resources/detail.html
        """
        type_template_map = {
            ResourceType.EXERCISE:     'apps/content/resources/exercise_detail.html',
            ResourceType.LESSON:       'apps/content/resources/lesson_detail.html',
            ResourceType.HOMEWORK:     'apps/content/resources/homework_detail.html',
            ResourceType.TEST:         'apps/content/resources/test_detail.html',
            ResourceType.EXAM:         'apps/content/resources/exam_detail.html',
            ResourceType.PAST_PAPER:   'apps/content/resources/exam_detail.html',
            ResourceType.MOCK_EXAM:    'apps/content/resources/exam_detail.html',
            ResourceType.FOREIGN_BOOK: 'apps/content/resources/book_detail.html',
            ResourceType.TEXTBOOK:     'apps/content/resources/book_detail.html',
            ResourceType.STUDY_GUIDE:  'apps/content/resources/book_detail.html',
        }
        resource_type = getattr(self, '_resource_type', None)
        return [
            type_template_map.get(resource_type, 'apps/content/resources/detail.html')
        ]

    def get_object(self, queryset=None):
        try:
            resource = get_resource_for_detail(self.kwargs['pk'])
        except Resource.DoesNotExist:
            raise Http404('Resource not found or not published.')

        # cache type for get_template_names
        self._resource_type = resource.resource_type

        logger.info(
            'ResourceDetailView accessed',
            extra={
                'user_id':     self.request.user.id if self.request.user.is_authenticated else None,
                'resource_pk': str(resource.pk),
                'type':        resource.resource_type,
            },
        )

        return resource

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.object
        user     = self.request.user

        # ── Breadcrumb context ────────────────────────────────────────────
        gs      = resource.course.effective_grade_subject if resource.course else None
        subject = gs.subject if gs else resource.subject
        grade   = gs.grade   if gs else None
        level   = grade.level if grade else (subject.level if subject else None)

        context.update({
            'subject': subject,
            'grade':   grade,
            'level':   level,
            'course':  resource.course,
        })

        # ── Student-specific context ──────────────────────────────────────
        is_student = (
            user.is_authenticated
            and getattr(user, 'is_student', False)
        )
        context['is_student'] = is_student

        if is_student:
            progress, _ = get_or_create_resource_progress(user, resource)
            context['progress']    = progress
            context['user_rating'] = get_resource_user_rating(user, resource)
        else:
            context['progress']    = None
            context['user_rating'] = None

        return context


def resource_download_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk, is_active=True)

    if not resource.file:
        raise Http404("File not found.")

    user = request.user

    # Only students increment download count
    if user.is_authenticated and getattr(user, "is_student", False):
        session_key = f"downloaded_resource_{resource.pk}"

        if not request.session.get(session_key, False):
            with transaction.atomic():
                resource.increment_download_count()

            request.session[session_key] = True

        content_type = ContentType.objects.get_for_model(
            Resource, for_concrete_model=False
        )

        progress, created = ContentProgress.objects.get_or_create(
            student=user,
            content_type=content_type,
            object_id=resource.pk,
        )

        # Only increment first time student downloads
        if created or not getattr(progress, "downloaded_at", None):
            with transaction.atomic():
                resource.increment_download_count()

                ContentProgress.objects.filter(pk=progress.pk).update(
                    downloaded_at=timezone.now()
                )

    # Serve file
    return FileResponse(
        resource.file.open("rb"),
        content_type=resource.file_mimetype or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{resource.original_filename}"'
        },
    )

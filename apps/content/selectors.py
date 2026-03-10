from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q

from .choices import ResourceType, ResourceStatus
from .models import Course, Resource
from apps.progress.models import ContentProgress
from apps.feedback.models import Rating

QUARTER_TO_TERM = {'q1': 'first', 'q2': 'second', 'q3': 'third'}


def get_course_by_pk(pk):
    return (
        Course.objects
        .select_related(
            'chapter',
            'chapter__grade_subject',
            'chapter__grade_subject__grade',
            'chapter__grade_subject__grade__level',
            'chapter__grade_subject__subject',
            'grade_subject',
            'grade_subject__grade',
            'grade_subject__grade__level',
            'grade_subject__subject',
        )
        .annotate(
            lessons_count   = Count(
                'resources',
                filter=Q(resources__resource_type=ResourceType.LESSON,
                         resources__status='published'),
                distinct=True,
            ),
            summaries_count = Count(
                'resources',
                filter=Q(resources__resource_type=ResourceType.SUMMARY,
                         resources__status='published'),
                distinct=True,
            ),
            homeworks_count = Count(
                'resources',
                filter=Q(resources__resource_type=ResourceType.HOMEWORK,
                         resources__status='published'),
                distinct=True,
            ),
            exercises_count = Count(
                'resources',
                filter=Q(resources__resource_type=ResourceType.EXERCISE,
                         resources__status='published'),
                distinct=True,
            ),
            notes_count     = Count(
                'resources',
                filter=Q(resources__resource_type=ResourceType.NOTES,
                         resources__status='published'),
                distinct=True,
            ),
            series_count    = Count(
                'resources',
                filter=Q(resources__resource_type=ResourceType.SERIES,
                         resources__status='published'),
                distinct=True,
            ),
            resources_count = Count(
                'resources',
                filter=Q(resources__status='published'),
                distinct=True,
            ),
            videos_count = Count(
                'videos',
                filter=Q(videos__is_active=True),
                distinct=True,
            ),
        )
        .get(pk=pk)
    )


def get_course_progress(student, course):
    """
    Returns ContentProgress for (student, course) or None.
    """

    course_ct = ContentType.objects.get_for_model(Course)
    return (
        ContentProgress.objects
        .filter(
            student=student,
            content_type=course_ct,
            object_id=course.pk,
        )
        .first()
    )


def get_or_create_course_progress(student, course):
    """
    Gets or creates ContentProgress for (student, course).
    Returns (progress, created).
    """

    course_ct = ContentType.objects.get_for_model(Course)
    return ContentProgress.objects.get_or_create(
        student=student,
        content_type=course_ct,
        object_id=course.pk,
    )


def resolve_course_breadcrumb(course):
    """
    Returns (level, grade, subject, chapter_or_none) from a course.
    Works for both chapter-based and standalone courses.
    """
    gs = course.effective_grade_subject
    return {
        'level':   gs.grade.level,
        'grade':   gs.grade,
        'subject': gs.subject,
        'chapter': course.chapter,
    }


def get_course_exercises(course, filters: dict, user=None):
    """
    Returns published exercises (ResourceType.EXERCISE) for a course.
    Applies search + filter params from the request.
    Attaches .progress_obj per resource for authenticated students.

    Args:
        course:  Course instance
        filters: dict from request.GET — keys: q, difficulty, has_solution, completed
        user:    request.user (may be anonymous)

    Returns:
        list of Resource instances (annotated with .progress_obj)
    """
    qs = (
        Resource.objects
        .filter(
            course=course,
            resource_type=ResourceType.EXERCISE,
            status=ResourceStatus.PUBLISHED,
        )
        .select_related('created_by')
        .order_by('order', '-created_at')
    )

    # ── Search ───────────────────────────────────────────────────────────
    q = filters.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(metadata__icontains=q)
        )

    # ── Difficulty ───────────────────────────────────────────────────────
    difficulty = filters.get('difficulty', '').strip()
    if difficulty:
        qs = qs.filter(difficulty=difficulty)

    # ── Has solution ─────────────────────────────────────────────────────
    has_solution = filters.get('has_solution', '')
    if has_solution == '1':
        qs = qs.filter(has_solution=True)
    elif has_solution == '0':
        qs = qs.filter(has_solution=False)

    # ── Completion filter (students only) ────────────────────────────────
    is_student = (
        user is not None
        and user.is_authenticated
        and getattr(user, 'is_student', False)
    )

    completed = filters.get('completed', '')
    if completed in ('0', '1') and is_student:

        resource_ct    = ContentType.objects.get_for_model(Resource)
        progress_ids   = (
            ContentProgress.objects
            .filter(
                student=user,
                content_type=resource_ct,
                is_completed=(completed == '1'),
            )
            .values_list('object_id', flat=True)
        )
        qs = qs.filter(id__in=progress_ids)

    # ── Attach progress objects (bulk, no N+1) ───────────────────────────
    resources = list(qs)

    if is_student and resources:

        resource_ct  = ContentType.objects.get_for_model(Resource)
        resource_ids = [r.id for r in resources]

        progress_map = {
            str(cp.object_id): cp
            for cp in ContentProgress.objects.filter(
                student=user,
                content_type=resource_ct,
                object_id__in=resource_ids,
            )
        }
        for resource in resources:
            resource.progress_obj = progress_map.get(str(resource.id))
    else:
        for resource in resources:
            resource.progress_obj = None

    return resources


def get_resource_for_detail(pk):
    """
    Fetches a published Resource with all relations needed
    for the detail page pre-loaded.
    """

    return (
        Resource.objects
        .select_related(
            'course',
            'course__chapter',
            'course__chapter__grade_subject__grade__level',
            'course__chapter__grade_subject__subject',
            'course__grade_subject__grade__level',
            'course__grade_subject__subject',
            'subject__level',
            'created_by',
        )
        .prefetch_related('tags')
        .get(pk=pk, status=ResourceStatus.PUBLISHED)
    )


def get_or_create_resource_progress(user, resource):
    """
    Gets or creates a ContentProgress entry for a student viewing a resource.
    Returns (progress, created).
    """

    resource_ct = ContentType.objects.get_for_model(Resource)

    return ContentProgress.objects.get_or_create(
        student=user,
        content_type=resource_ct,
        object_id=resource.pk,
        defaults={
            'is_completed':    False,
            'first_viewed_at': timezone.now(),
        },
    )


def get_resource_user_rating(user, resource):
    """
    Returns the user's Rating for this resource, or None.
    Silently returns None if the Rating model doesn't exist yet.
    """
    try:

        resource_ct = ContentType.objects.get_for_model(Resource)

        return Rating.objects.filter(
            user=user,
            content_type=resource_ct,
            object_id=resource.pk,
            active=True,
        ).first()
    except Exception:
        return None


def get_subject_resource_counts_by_quarter(subject):
    """
    Returns counts for each resource type per quarter for a subject.

    Structure:
    {
        'q1': {'courses': 5, 'test': 2, 'exam': 1, ...},
        'q2': {...},
        'q3': {...},
    }
    """
    result = {}

    for quarter, term in QUARTER_TO_TERM.items():

        # Count courses via GradeSubject → Chapter → Course
        courses_count = Course.objects.filter(
            Q(grade_subject__subject=subject, term=term)
            | Q(chapter__grade_subject__subject=subject, chapter__term=term)
        ).filter(is_active=True).distinct().count()

        # Count subject-level resources per type for this term
        subject_resources = (
            Resource.objects
            .filter(subject=subject, term=term, status='published')
            .values('resource_type')
            .annotate(count=Count('id'))
        )
        type_counts = {row['resource_type']: row['count'] for row in subject_resources}

        result[quarter] = {
            'courses':      courses_count,
            'test':         type_counts.get(ResourceType.TEST,         0),
            'exam':         type_counts.get(ResourceType.EXAM,         0),
            'past_paper':   type_counts.get(ResourceType.PAST_PAPER,   0),
            'mock_exam':    type_counts.get(ResourceType.MOCK_EXAM,    0),
            'textbook':     type_counts.get(ResourceType.TEXTBOOK,     0),
            'foreign_book': type_counts.get(ResourceType.FOREIGN_BOOK, 0),
            'study_guide':  type_counts.get(ResourceType.STUDY_GUIDE,  0),
        }

    return result


def get_course_resources(course, resource_type, filters=None, user=None):
    """
    Generic resource selector for any course resource type.
    Supports filters: q, difficulty, has_solution, completed.
    """
    qs = (
        Resource.objects
        .filter(
            course=course,
            resource_type=resource_type,
            status=ResourceStatus.PUBLISHED,
        )
        .order_by('order')
    )

    if filters:
        q            = filters.get('q', '').strip()
        difficulty   = filters.get('difficulty', '')
        has_solution = filters.get('has_solution', '')
        completed    = filters.get('completed', '')

        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(metadata__icontains=q)
            )
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if has_solution == '1':
            qs = qs.filter(has_solution=True)
        elif has_solution == '0':
            qs = qs.filter(has_solution=False)

        if completed and user and user.is_authenticated:
            content_type = ContentType.objects.get_for_model(Resource)
            completed_ids = ContentProgress.objects.filter(
                student=user,
                content_type=content_type,
                is_completed=completed == '1',
            ).values_list('object_id', flat=True)
            qs = qs.filter(pk__in=completed_ids)

    # Attach progress per resource (bulk — no N+1)
    if user and user.is_authenticated and getattr(user, 'is_student', False):
        content_type = ContentType.objects.get_for_model(Resource)
        progress_map = {
            str(cp.object_id): cp
            for cp in ContentProgress.objects.filter(
                student=user,
                content_type=content_type,
                object_id__in=qs.values_list('pk', flat=True),
            )
        }
        for resource in qs:
            resource.progress_obj = progress_map.get(str(resource.pk))
    else:
        for resource in qs:
            resource.progress_obj = None

    return qs
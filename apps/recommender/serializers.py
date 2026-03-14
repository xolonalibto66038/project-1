# recommendations/serializers.py

from rest_framework import serializers


class RecommendedResourceSerializer(serializers.Serializer):
    """
    Renders a Resource instance as a recommendation card.
    """

    id = serializers.UUIDField()
    title = serializers.CharField()
    slug = serializers.SlugField()
    resource_type = serializers.CharField()
    difficulty = serializers.CharField()
    term = serializers.CharField()
    is_free = serializers.BooleanField()
    download_count = serializers.IntegerField()
    view_count = serializers.IntegerField()
    has_solution = serializers.BooleanField()

    # File presence — frontend uses these to decide which icon/CTA to show
    has_file = serializers.SerializerMethodField()

    # Metadata fields — safely pulled from the JSONField
    duration_minutes = serializers.SerializerMethodField()
    total_marks = serializers.SerializerMethodField()
    coefficient = serializers.SerializerMethodField()

    # Context breadcrumb — enough for the card subtitle
    grade_subject = serializers.SerializerMethodField()

    def get_has_file(self, obj) -> bool:
        return bool(obj.file)

    def get_duration_minutes(self, obj):
        return obj.metadata.get("duration_minutes")

    def get_total_marks(self, obj):
        return obj.metadata.get("total_marks")

    def get_coefficient(self, obj):
        return obj.metadata.get("coefficient")

    def get_grade_subject(self, obj) -> str:
        """
        Returns a short human-readable label for the card subtitle.
        e.g. "3AM - Math" or "1AS - Physique [SE]"
        Resolves through course if the resource is course-attached.
        """
        gs = None
        if obj.course_id:
            course = obj.course
            if course.chapter_id:
                gs = course.chapter.grade_subject
            else:
                gs = course.grade_subject
        else:
            gs = obj.grade_subject

        if gs is None:
            return ""

        spec = f" [{gs.specialty.short_name}]" if gs.specialty_id else ""
        return f"{gs.grade.short_name} - {gs.subject.short_name}{spec}"


class RecommendedCourseSerializer(serializers.Serializer):
    """
    Renders a Course instance as a recommendation card.
    """

    id = serializers.UUIDField()
    title = serializers.CharField()
    slug = serializers.SlugField()
    difficulty = serializers.CharField()
    term = serializers.SerializerMethodField()
    description = serializers.CharField()
    is_active = serializers.BooleanField()

    # Context breadcrumb
    grade_subject = serializers.SerializerMethodField()
    chapter = serializers.SerializerMethodField()

    def get_term(self, obj) -> str | None:
        """Uses the Course.effective_term property to handle chapter inheritance."""
        return obj.effective_term or None

    def get_grade_subject(self, obj) -> str:
        gs = obj.chapter.grade_subject if obj.chapter_id else obj.grade_subject
        if gs is None:
            return ""
        spec = f" [{gs.specialty.short_name}]" if gs.specialty_id else ""
        return f"{gs.grade.short_name} - {gs.subject.short_name}{spec}"

    def get_chapter(self, obj) -> str | None:
        if obj.chapter_id:
            return obj.chapter.title
        return None


# ── Generic dispatcher ─────────────────────────────────────────────────────────

_SERIALIZER_MAP: dict[str, type] = {
    "resource": RecommendedResourceSerializer,
    "course": RecommendedCourseSerializer,
}


class RecommendedItemSerializer(serializers.Serializer):
    """
    Generic envelope serializer for any recommended item.

    Dispatches to the correct type-specific serializer based on the
    instance's class name. Wraps the result in a typed envelope so the
    frontend always knows what shape it received:

        {
            "item_type": "resource",
            "data": { ...RecommendedResourceSerializer fields... }
        }

    Usage (in a view):
        results = recommendation_service.similar_to(resource)
        serializer = RecommendedItemSerializer(results, many=True)
    """

    item_type = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()

    def get_item_type(self, obj) -> str:
        return obj.__class__.__name__.lower()

    def get_data(self, obj) -> dict:
        label = obj.__class__.__name__.lower()
        serializer_class = _SERIALIZER_MAP.get(label)

        if serializer_class is None:
            # Unregistered type — return a safe minimal fallback
            # so one unknown type doesn't break the entire list.
            return {
                "id": str(obj.pk),
                "title": getattr(obj, "title", str(obj)),
            }

        return serializer_class(obj, context=self.context).data

from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Quiz
from .quiz_question import QuizQuestionInline


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin interface for Quiz model"""

    # List view configuration
    list_display = (
        "title",
        "created_by",
        "question_count_display",
        "total_points_display",
        "is_published",
        "availability_status",
        "passing_score",
        "max_attempts",
        "created_at",
    )

    list_filter = (
        "is_published",
        "created_at",
        "start_date",
        "end_date",
        "randomize_questions",
        "show_results_immediately",
        "allow_review",
        "created_by",
    )

    search_fields = (
        "title",
        "description",
        "created_by__username",
        "created_by__email",
    )

    # Form configuration
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "description", "instructions", "subject", "course")},
        ),
        (
            "Quiz Settings",
            {
                "fields": (
                    "time_limit",
                    "max_attempts",
                    "passing_score",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Availability",
            {
                "fields": (
                    "is_published",
                    "start_date",
                    "end_date",
                ),
            },
        ),
        (
            "Behavior Settings",
            {
                "fields": (
                    "randomize_questions",
                    "show_results_immediately",
                    "allow_review",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_by",),
                "classes": ("collapse",),
            },
        ),
    )

    # Add inline for questions
    inlines = [QuizQuestionInline]

    # Read-only fields
    readonly_fields = ("created_at", "updated_at")

    # Ordering
    ordering = ("-created_at",)

    # Pagination
    list_per_page = 15
    list_max_show_all = 100

    # Advanced features
    save_on_top = True
    preserve_filters = True

    # Custom actions
    actions = ["publish_quizzes", "unpublish_quizzes", "duplicate_quiz"]

    def get_fieldsets(self, request, obj=None):
        """Add created/updated timestamps for existing objects"""
        fieldsets = list(self.fieldsets)
        if obj:  # editing existing object
            fieldsets[-1] = (
                "Metadata",
                {
                    "fields": ("created_by", "created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Make created_by readonly for non-superusers when editing"""
        readonly_fields = list(self.readonly_fields)
        if obj and not request.user.is_superuser:
            readonly_fields.append("created_by")
        return readonly_fields

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user for new quizzes"""
        if not change:  # new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def question_count_display(self, obj):
        """Display question count with link to questions"""
        count = obj.question_count
        if count > 0:
            return format_html(
                '<a href="{}?quiz__id__exact={}" title="View questions">{} questions</a>',
                reverse(
                    "admin:assessment_quizquestion_changelist"
                ),  # Replace 'your_app' with actual app name
                obj.id,
                count,
            )
        return "0 questions"

    question_count_display.short_description = "Questions"
    question_count_display.admin_order_field = "quiz_questions__count"

    def total_points_display(self, obj):
        """Display total possible points"""
        total = obj.total_points
        return f"{total} pts" if total else "0 pts"

    total_points_display.short_description = "Total Points"

    def availability_status(self, obj):
        """Show availability status with color coding"""
        if not obj.is_published:
            return format_html('<span style="color: #888;">Draft</span>')

        now = timezone.now()

        if obj.start_date and now < obj.start_date:
            return format_html('<span style="color: #ff9500;">Scheduled</span>')
        elif obj.end_date and now > obj.end_date:
            return format_html('<span style="color: #dc3545;">Expired</span>')
        else:
            return format_html('<span style="color: #28a745;">Available</span>')

    availability_status.short_description = "Status"

    # Custom actions
    def publish_quizzes(self, request, queryset):
        """Bulk publish selected quizzes"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} quiz(es) were published.")

    publish_quizzes.short_description = "Publish selected quizzes"

    def unpublish_quizzes(self, request, queryset):
        """Bulk unpublish selected quizzes"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} quiz(es) were unpublished.")

    unpublish_quizzes.short_description = "Unpublish selected quizzes"

    def duplicate_quiz(self, request, queryset):
        """Duplicate selected quizzes"""
        duplicated = 0
        for quiz in queryset:
            questions = list(quiz.quiz_questions.all())
            quiz.pk = None
            quiz.title = f"Copy of {quiz.title}"
            quiz.is_published = False
            quiz.created_by = request.user
            quiz.save()
            for qq in questions:
                qq.pk = None
                qq.quiz = quiz
                qq.save()
            duplicated += 1

        self.message_user(
            request, _(f"{duplicated} quiz(es) duplicated."), messages.SUCCESS
        )

    duplicate_quiz.short_description = "Duplicate selected quizzes"

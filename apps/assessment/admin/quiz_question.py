from django.contrib import admin
from django.utils.html import format_html

from ..models import QuizQuestion


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    """Admin interface for QuizQuestion model"""

    list_display = (
        "quiz",
        "order",
        "question_type",
        "question_preview",
        "effective_points_display",
    )

    list_filter = (
        "quiz",
        "question_content_type",
        "order",
    )

    search_fields = (
        "quiz__title",
        "question_object_id",
    )

    autocomplete_fields = ["quiz"]

    fields = (
        "quiz",
        "question_content_type",
        "question_object_id",
        "order",
        "points_override",
        "question_details",
    )

    readonly_fields = ("question_details",)

    ordering = ("quiz", "order")

    # Pagination
    list_per_page = 15
    list_max_show_all = 100

    # Advanced features
    save_on_top = True
    preserve_filters = True

    def question_type(self, obj):
        """Display the question type"""
        return (
            obj.question_content_type.model.title()
            if obj.question_content_type
            else "Unknown"
        )

    question_type.short_description = "Question Type"

    def question_preview(self, obj):
        """Show a preview of the question"""
        if obj.question:
            question_text = str(obj.question)
            if len(question_text) > 80:
                question_text = question_text[:80] + "..."
            return question_text
        return "No question"

    question_preview.short_description = "Question Preview"

    def effective_points_display(self, obj):
        """Display effective points (override or default)"""
        points = obj.effective_points
        if obj.points_override:
            return format_html("<strong>{} pts</strong> (override)", points)
        return f"{points} pts"

    effective_points_display.short_description = "Points"

    def question_details(self, obj):
        """Show detailed question information"""
        if not obj.question:
            return "No question selected"

        details = []
        details.append(
            f"<strong>Type:</strong> {obj.question_content_type.model.title()}"
        )
        details.append(f"<strong>ID:</strong> {obj.question_object_id}")
        details.append(f"<strong>Question:</strong> {obj.question}")

        if hasattr(obj.question, "points"):
            details.append(f"<strong>Default Points:</strong> {obj.question.points}")

        if obj.points_override:
            details.append(f"<strong>Override Points:</strong> {obj.points_override}")

        return format_html("<br>".join(details))

    question_details.short_description = "Question Details"


class QuizQuestionInline(admin.TabularInline):
    """Inline admin for managing quiz questions within the quiz admin"""

    model = QuizQuestion
    extra = 0
    min_num = 0
    fields = (
        "question_content_type",
        "question_object_id",
        "order",
        "points_override",
        "question_preview",
    )
    readonly_fields = ("question_preview",)
    ordering = ("order",)

    def question_preview(self, obj):
        """Show a preview of the question content"""
        if obj.question:
            # Truncate long questions for preview
            question_text = str(obj.question)
            if len(question_text) > 100:
                question_text = question_text[:100] + "..."
            return format_html(
                '<span title="{}">{}</span>', str(obj.question), question_text
            )
        return "No question selected"

    question_preview.short_description = "Question Preview"

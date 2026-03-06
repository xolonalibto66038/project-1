from django.contrib import admin
from django.utils.html import format_html

from ..filters import LengthRangeFilter
from ..models import EssayQuestion
from .question import BaseQuestionAdmin


@admin.register(EssayQuestion)
class TextQuestionAdmin(BaseQuestionAdmin):
    """
    Admin interface for TextQuestion model
    """

    list_display = [
        "title",
        "question_type_display",
        "points",
        "difficulty_level",
        "length_limits",
        "auto_gradable_display",
        "created_by",
        "is_active",
        "created_at",
    ]

    list_filter = [
        "difficulty_level",
        "is_active",
        "is_auto_gradable",
        "created_at",
        LengthRangeFilter,  # Custom filter defined below
    ]

    search_fields = [
        "title",
        "question_text",
        "sample_answer",
        "keywords",
        "explanation",
        "tags",
        "created_by__username",
    ]

    # Read-only fields
    readonly_fields = (
        "created_at",
        "updated_at",
        "length_preview",
        "sample_length_info",
        "keywords_preview",
    )

    # Ordering
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Question Content",
            {
                "fields": (
                    "title",
                    "question_text",
                ),
                "description": "Basic question information",
            },
        ),
        (
            "Answer Settings",
            {
                "fields": (
                    "min_length",
                    "max_length",
                    "sample_answer",
                    "sample_length_info",
                ),
                "description": "Configure answer length requirements and provide sample answer",
            },
        ),
        (
            "Auto-Grading",
            {
                "fields": (
                    "is_auto_gradable",
                    "keywords",
                    "keywords_preview",
                    "tags",
                ),
                "description": "Enable automatic grading with keywords (comma-separated)",
                "classes": ("collapse",),
            },
        ),
        ("Question Settings", {"fields": ("points", "difficulty_level", "is_active")}),
        (
            "Additional Information",
            {
                "fields": ("explanation",),
                "classes": ("wide",),
            },
        ),
        (
            "Metadata",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # Pagination
    list_per_page = 25

    def length_limits(self, obj):
        """Display min/max length limits"""
        return f"{obj.min_length} - {obj.max_length} chars"

    length_limits.short_description = "Length Limits"

    def auto_gradable_display(self, obj):
        """Display auto-gradable status with icon"""
        if obj.is_auto_gradable:
            return format_html('<span style="color: #28a745;">✓ Auto</span>')
        return format_html('<span style="color: #dc3545;">✗ Manual</span>')

    auto_gradable_display.short_description = "Grading"

    def keywords_preview(self, obj):
        """Show a formatted preview of keywords"""
        if obj.keywords:
            keywords_list = obj.get_keywords_list()
            if len(keywords_list) > 5:
                preview = (
                    ", ".join(keywords_list[:5]) + f", ... ({len(keywords_list)} total)"
                )
            else:
                preview = ", ".join(keywords_list)

            return format_html(
                '<div style="font-family: monospace; background: #f8f9fa; padding: 8px; border-radius: 4px;">'
                "{}"
                "</div>",
                preview,
            )
        return "No keywords defined"

    keywords_preview.short_description = "Keywords Preview"

    # Read-only field methods
    def length_preview(self, obj):
        """Show a preview of the length constraints"""
        if obj.min_length and obj.max_length:
            return format_html(
                "Students must write between <strong>{}</strong> and <strong>{}</strong> characters.<br>"
                '<small style="color: #666;">Sample ranges: '
                "Tweet (~280), Paragraph (~500), Short essay (~1000), Long essay (~2000+)</small>",
                obj.min_length,
                obj.max_length,
            )
        return "Length constraints not set"

    length_preview.short_description = "Length Constraint Preview"

    def sample_length_info(self, obj):
        """Show information about the sample answer length"""
        if obj.sample_answer:
            length = len(obj.sample_answer.strip())
            within_range = obj.validate_answer_length(obj.sample_answer)

            color = "#28a745" if within_range else "#dc3545"
            status = "Within range" if within_range else "Outside range"

            return format_html(
                'Sample answer length: <strong style="color: {};">{} characters</strong> ({})',
                color,
                length,
                status,
            )
        return "No sample answer provided"

    sample_length_info.short_description = "Sample Answer Length"

    def get_form(self, request, obj=None, **kwargs):
        """Customize form behavior"""
        form = super().get_form(request, obj, **kwargs)

        # Add help text for keywords field
        if "keywords" in form.base_fields:
            form.base_fields["keywords"].help_text = (
                "Enter keywords separated by commas. Example: 'python, programming, code'. "
                "Student answers containing these keywords will receive partial/full credit."
            )

        return form

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for non-superusers"""
        readonly_fields = list(super().get_readonly_fields(request, obj))

        if not request.user.is_superuser:
            readonly_fields.extend(["created_by"])

        return readonly_fields

    actions = [
        "make_active",
        "make_inactive",
        "enable_auto_grading",
        "disable_auto_grading",
        "duplicate_questions",
        "export_questions",
        "validate_sample_answers",
    ]

    def make_active(self, request, queryset):
        """Bulk action to activate questions"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} questions were successfully activated.")

    make_active.short_description = "Mark selected questions as active"

    def make_inactive(self, request, queryset):
        """Bulk action to deactivate questions"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f"{updated} questions were successfully deactivated."
        )

    make_inactive.short_description = "Mark selected questions as inactive"

    def enable_auto_grading(self, request, queryset):
        """Bulk action to enable auto-grading"""
        updated = queryset.update(is_auto_gradable=True)
        self.message_user(request, f"Auto-grading enabled for {updated} questions.")

    enable_auto_grading.short_description = "Enable auto-grading for selected questions"

    def disable_auto_grading(self, request, queryset):
        """Bulk action to disable auto-grading"""
        updated = queryset.update(is_auto_gradable=False)
        self.message_user(request, f"Auto-grading disabled for {updated} questions.")

    disable_auto_grading.short_description = (
        "Disable auto-grading for selected questions"
    )

    def export_questions(self, request, queryset):
        """Export questions (placeholder for actual implementation)"""
        self.message_user(
            request,
            f"Export functionality would export {queryset.count()} text question(s). "
            "Implement CSV/JSON export as needed.",
        )

    export_questions.short_description = "Export questions"

    def validate_sample_answers(self, request, queryset):
        """Check if sample answers meet length requirements"""
        issues = []
        for question in queryset:
            if question.sample_answer:
                if not question.validate_answer_length(question.sample_answer):
                    issues.append(f'"{question.title}" - sample answer length issue')

        if issues:
            self.message_user(
                request,
                f"Found {len(issues)} questions with sample answer length issues. "
                f"Check the sample length info field for details.",
                level="warning",
            )
        else:
            self.message_user(
                request,
                f"All {queryset.count()} selected questions have valid sample answers.",
            )

    validate_sample_answers.short_description = "Validate sample answer lengths"

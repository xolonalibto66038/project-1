from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from ..filters import AttemptGradeFilter
from .forms import AttemptForm
from ..models import Attempt


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    """Admin interface for Attempt model"""

    form = AttemptForm

    # List view configuration
    list_display = (
        "user_quiz_display",
        "student",
        "attempt_number",
        "status_display",
        "score_display",
        "grade_display",
        "time_taken_display",
        "started_at",
        "grading_status",
    )

    list_filter = (
        "is_completed",
        "is_timed_out",
        "is_graded",
        # "is_passed",
        "started_at",
        "submitted_at",
        "quiz",
        "quiz__created_by",
        AttemptGradeFilter,  # Custom filter defined below
    )

    search_fields = (
        "student__email",
        "student__first_name",
        "student__last_name",
        "quiz__title",
        "notes",
    )

    autocomplete_fields = ["student", "quiz"]

    # Form configuration
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "student",
                    "quiz",
                    "attempt_number",
                )
            },
        ),
        (
            "Timing & Status",
            {
                "fields": (
                    # "started_at",
                    "submitted_at",
                    "time_taken",
                    "is_completed",
                    "is_timed_out",
                ),
            },
        ),
        (
            "Scoring",
            {
                "fields": (
                    "total_points_possible",
                    "total_points_earned",
                    "score_percentage",
                    "grade_letter_display",
                    "passed_status",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Grading Status",
            {
                "fields": (
                    "is_graded",
                    "auto_graded_at",
                    "manually_graded_at",
                    "graded_by",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Technical Information",
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Additional Notes",
            {
                "fields": ("notes",),
                "classes": ("collapse",),
            },
        ),
    )

    # Read-only fields
    readonly_fields = (
        "started_at",
        "time_taken",
        "grade_letter_display",
        "passed_status",
        "ip_address",
        "user_agent",
    )

    # Ordering
    ordering = ("-started_at",)

    # Pagination
    list_per_page = 15
    list_max_show_all = 100

    # Advanced features
    save_on_top = True
    preserve_filters = True

    # Custom actions
    actions = [
        "mark_as_graded",
        "recalculate_scores",
        "export_results",
        "auto_submit_expired",
    ]

    # Date hierarchy
    date_hierarchy = "started_at"

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on attempt status"""
        readonly_fields = list(self.readonly_fields)

        if obj and obj.is_completed:
            # Don't allow editing core data for completed attempts
            readonly_fields.extend(
                [
                    "student",
                    "quiz",
                    "attempt_number",
                    "submitted_at",
                    "is_completed",
                    "is_timed_out",
                    "total_points_possible",
                    "total_points_earned",
                    "score_percentage",
                ]
            )

        return readonly_fields

    def user_quiz_display(self, obj):
        """Display user and quiz in a compact format"""
        return format_html(
            "<strong>{}</strong><br><small>{}</small>",
            obj.student.get_full_name() or obj.student.email,
            obj.quiz.title[:50] + ("..." if len(obj.quiz.title) > 50 else ""),
        )

    user_quiz_display.short_description = "User / Quiz"
    user_quiz_display.admin_order_field = "student__user__username"

    def status_display(self, obj):
        """Display attempt status with color coding"""
        if obj.is_completed:
            if obj.is_timed_out:
                return format_html(
                    '<span style="color: #ff9500; font-weight: bold;">⏰ Timed Out</span>'
                )
            else:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">✓ Completed</span>'
                )
        else:
            if obj.is_expired:
                return format_html(
                    '<span style="color: #dc3545; font-weight: bold;">⚠ Expired</span>'
                )
            else:
                return format_html(
                    '<span style="color: #007bff; font-weight: bold;">⏳ In Progress</span>'
                )

    status_display.short_description = "Status"
    status_display.admin_order_field = "is_completed"

    def score_display(self, obj):
        """Display score with visual indicators"""
        if not obj.is_completed:
            return format_html('<span style="color: #6c757d;">—</span>')

        try:
            percentage = float(obj.score_percentage)
        except (TypeError, ValueError):
            percentage = 0.0

        try:
            earned = float(obj.total_points_earned)
        except (TypeError, ValueError):
            earned = 0.0

        try:
            possible = float(obj.total_points_possible)
        except (TypeError, ValueError):
            possible = 0.0

        color = "#28a745" if obj.is_passed else "#dc3545"

        formatted = (
            f'<span style="color: {color}; font-weight: bold;">{percentage:.1f}%</span><br>'
            f"<small>{earned}/{possible} pts</small>"
        )
        return format_html(formatted)

    score_display.short_description = "Score"
    score_display.admin_order_field = "score_percentage"

    def grade_display(self, obj):
        """Display letter grade with color coding"""
        if not obj.is_completed:
            return format_html('<span style="color: #6c757d;">—</span>')

        grade = obj.get_grade_letter()
        color = {
            "A": "#28a745",
            "B": "#20c997",
            "C": "#ffc107",
            "D": "#fd7e14",
            "F": "#dc3545",
        }.get(grade, "#6c757d")

        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 16px;">{}</span>',
            color,
            grade,
        )

    grade_display.short_description = "Grade"
    grade_display.admin_order_field = "score_percentage"

    def time_taken_display(self, obj):
        """Display time taken in a readable format"""
        if not obj.time_taken:
            if obj.is_completed:
                return "Unknown"
            else:
                # Show elapsed time for in-progress attempts
                elapsed = timezone.now() - obj.started_at
                return format_html(
                    '<span style="color: #007bff;">{} (ongoing)</span>',
                    self._format_duration(elapsed),
                )

        time_str = self._format_duration(obj.time_taken)

        # Color code based on time limit
        if obj.quiz.time_limit:
            time_limit = timezone.timedelta(minutes=obj.quiz.time_limit)
            if obj.time_taken > time_limit:
                return format_html(
                    '<span style="color: #dc3545;">{} (over limit)</span>', time_str
                )

        return time_str

    time_taken_display.short_description = "Time Taken"
    time_taken_display.admin_order_field = "time_taken"

    def grading_status(self, obj):
        """Display grading status"""
        if not obj.is_completed:
            return format_html('<span style="color: #6c757d;">Pending</span>')

        if obj.is_graded:
            if obj.manually_graded_at:
                return format_html(
                    '<span style="color: #28a745;">✓ Manual</span><br>'
                    "<small>by {}</small>",
                    obj.graded_by.user.get_full_name() if obj.graded_by else "Unknown",
                )
            else:
                return format_html('<span style="color: #007bff;">✓ Auto</span>')
        else:
            return format_html('<span style="color: #ffc107;">⏳ Pending</span>')

    grading_status.short_description = "Grading"
    grading_status.admin_order_field = "is_graded"

    def grade_letter_display(self, obj):
        """Read-only display of grade letter"""
        if obj.is_completed:
            return obj.get_grade_letter()
        return "Not completed"

    grade_letter_display.short_description = "Letter Grade"

    def passed_status(self, obj):
        """Display pass/fail status"""
        if not obj.is_completed:
            return "Not completed"

        if obj.is_passed:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ PASSED</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ FAILED</span>'
            )

    passed_status.short_description = "Pass Status"

    def _format_duration(self, duration):
        """Format duration in a readable way"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    # Custom Actions
    def mark_as_graded(self, request, queryset):
        """Mark selected attempts as graded"""
        updated = queryset.update(
            is_graded=True, manually_graded_at=timezone.now(), graded_by=request.user
        )
        self.message_user(request, f"{updated} attempt(s) marked as graded.")

    mark_as_graded.short_description = "Mark as manually graded"

    def recalculate_scores(self, request, queryset):
        """Recalculate scores for selected attempts"""
        count = 0
        for attempt in queryset:
            if attempt.is_completed:
                attempt.calculate_score()
                attempt.save()
                count += 1

        self.message_user(request, f"Scores recalculated for {count} attempt(s).")

    recalculate_scores.short_description = "Recalculate scores"

    def auto_submit_expired(self, request, queryset):
        """Auto-submit expired attempts"""
        count = 0
        for attempt in queryset.filter(is_completed=False):
            if attempt.is_expired:
                attempt.submit(auto_submit=True)
                count += 1

        self.message_user(request, f"{count} expired attempt(s) auto-submitted.")

    auto_submit_expired.short_description = "Auto-submit expired attempts"

    def export_results(self, request, queryset):
        """Export attempt results (placeholder - implement as needed)"""
        # This would typically generate a CSV/Excel file
        self.message_user(
            request,
            f"Export functionality would export {queryset.count()} attempt(s). "
            "Implement CSV/Excel export as needed.",
        )

    export_results.short_description = "Export results"


# Inline for use in other admin interfaces (like User admin)
class AttemptInline(admin.TabularInline):
    """Inline admin for showing attempts in other models"""

    model = Attempt
    extra = 0
    can_delete = False
    fields = (
        "quiz",
        "attempt_number",
        "status_display",
        "score_percentage",
        "started_at",
    )
    readonly_fields = ("status_display",)

    def status_display(self, obj):
        if obj.is_completed:
            return "✓ Completed" if not obj.is_timed_out else "⏰ Timed Out"
        return "⏳ In Progress"

    status_display.short_description = "Status"

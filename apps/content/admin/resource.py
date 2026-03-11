# apps/content/admin/resource_admin.py

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..choices import ResourceStatus
from ..models import Course, Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display = (
        "title",
        "resource_type",
        "parent_display",
        "status",
        "difficulty",
        "term",
        "is_free",
        "has_solution",
        "file_display",
        "order",
    )
    list_display_links = ("title",)
    list_filter = (
        "resource_type",
        "status",
        "difficulty",
        "term",
        "is_free",
        "has_solution",
        "course__chapter__grade_subject__grade__level",
        "course__chapter__grade_subject__grade",
        "course__chapter__grade_subject__subject",
    )
    search_fields = ("title", "slug", "course__title", "grade_subject__subject__name")
    list_editable = ("status", "order", "is_free")
    ordering = ("course", "order")
    list_per_page = 25
    list_max_show_all = 200

    # ── Detail view ──
    readonly_fields = ("slug",)
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("course", "grade_subject")

    fieldsets = (
        (
            _("Parent"),
            {
                "fields": ("course", "grade_subject", "tags"),
                "description": _(
                    "Assign to a course (lesson/exercise/homework) OR "
                    "directly to a grade subject (test/exam/past paper). Never both."
                ),
            },
        ),
        (
            _("Identity"),
            {
                "fields": (
                    "title",
                    "slug",
                    "resource_type",
                    "order",
                    "term",
                    "created_by",
                ),
            },
        ),
        (
            _("Settings"),
            {
                "fields": ("status", "difficulty", "is_free"),
            },
        ),
        (
            _("Files"),
            {
                "fields": ("file", "solution_file", "has_solution"),
                "description": _(
                    "Upload the main resource file and optionally a separate solution file."
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
                "description": _(
                    "Type-specific JSON attributes. "
                    'e.g. {"duration_minutes": 60, "total_marks": 20}'
                ),
            },
        ),
    )

    # ── Custom display methods ──

    @admin.display(description=_("Parent"))
    def parent_display(self, obj):
        if obj.course:
            url = reverse("admin:content_course_change", args=[obj.course.pk])
            return format_html('<a href="{}">📘 {}</a>', url, obj.course.title)
        if obj.grade_subject:
            url = reverse(
                "admin:curriculum_gradesubject_change", args=[obj.grade_subject.pk]
            )
            return format_html(
                '<a href="{}">📚 {}</a>', url, obj.grade_subject.subject.name
            )
        return "—"

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            ResourceStatus.DRAFT: "#6c757d",
            ResourceStatus.PUBLISHED: "#28a745",
            ResourceStatus.ARCHIVED: "#dc3545",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="'
            "background:{}; color:#fff; padding:2px 8px; "
            'border-radius:4px; font-size:0.85em;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description=_("File"))
    def file_display(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📄 Download</a>', obj.file.url
            )
        return "—"

    # ── Custom actions ──

    @admin.action(description=_("Publish selected resources"))
    def publish(self, request, queryset):
        updated = queryset.update(status=ResourceStatus.PUBLISHED)
        self.message_user(
            request, _(f"{updated} resource(s) published."), messages.SUCCESS
        )

    @admin.action(description=_("Archive selected resources"))
    def archive(self, request, queryset):
        updated = queryset.update(status=ResourceStatus.ARCHIVED)
        self.message_user(
            request, _(f"{updated} resource(s) archived."), messages.SUCCESS
        )

    @admin.action(description=_("Mark selected as Draft"))
    def mark_draft(self, request, queryset):
        updated = queryset.update(status=ResourceStatus.DRAFT)
        self.message_user(
            request, _(f"{updated} resource(s) set to draft."), messages.SUCCESS
        )

    @admin.action(description=_("Mark selected as Free"))
    def mark_free(self, request, queryset):
        updated = queryset.update(is_free=True)
        self.message_user(
            request, _(f"{updated} resource(s) marked as free."), messages.SUCCESS
        )

    @admin.action(description=_("Reset slugs for selected resources"))
    def reset_slugs(self, request, queryset):
        for obj in queryset:
            obj.slug = ""
            obj.save()
        self.message_user(request, _("Slugs reset and regenerated."), messages.SUCCESS)

    actions = ["publish", "archive", "mark_draft", "mark_free", "reset_slugs"]

    # ── Custom URLs ──

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:pk>/duplicate/",
                self.admin_site.admin_view(self.duplicate_view),
                name="content_resource_duplicate",
            ),
        ]
        return custom + urls

    def duplicate_view(self, request, pk):
        obj = self.get_object(request, pk)
        if obj:
            obj.pk = None
            obj.slug = ""
            obj.status = ResourceStatus.DRAFT
            obj.title = f"{obj.title} (copy)"
            obj.save()
            self.message_user(
                request, _("Resource duplicated as draft."), messages.SUCCESS
            )
        return HttpResponseRedirect(reverse("admin:content_resource_changelist"))


class ResourceInline(admin.TabularInline):
    model = Course.resources.field.model
    extra = 0
    fields = ("title", "resource_type", "status", "difficulty", "order", "is_free")
    readonly_fields = ("slug",)
    ordering = ("order",)
    show_change_link = True

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "short_name",
        "level",
        "icon_display",
        "slug",
        "grade_count",
        "edit_button",
        "delete_button",
    )
    list_display_links = ("name",)
    list_filter = ("level",)
    search_fields = ("name", "short_name", "slug")
    list_editable = ("short_name",)
    ordering = ("level__order", "name")
    list_per_page = 20
    list_max_show_all = 100
    readonly_fields = ("slug",)
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("level",)

    fieldsets = (
        (
            _("General Information"),
            {
                "fields": ("level", "name", "short_name", "slug"),
                "description": _("Core subject information."),
            },
        ),
        (
            _("Display"),
            {
                "fields": ("icon",),
                "description": _("UI display settings for this subject."),
            },
        ),
    )

    # ── Custom display methods ──

    @admin.display(description=_("Icon"))
    def icon_display(self, obj):
        if obj.icon:
            return format_html(
                '<i class="{}" style="font-size:1.2rem;"></i> {}', obj.icon, obj.icon
            )
        return "—"

    @admin.display(description=_("Grades"))
    def grade_count(self, obj):
        count = obj.grade_subjects.count()
        url = (
            reverse("admin:curriculum_gradesubject_changelist")
            + f"?subject__id__exact={obj.pk}"
        )
        return format_html('<a href="{}">{} grade(s)</a>', url, count)

    # ── Custom actions ──

    @admin.action(description=_("Reset slugs for selected subjects"))
    def reset_slugs(self, request, queryset):
        for obj in queryset:
            obj.slug = ""
            obj.save()
        self.message_user(
            request, _("Slugs have been reset and regenerated."), messages.SUCCESS
        )

    actions = ["reset_slugs"]

    def edit_button(self, obj: Subject) -> str:
        """Render an Edit button linking to the change page for the object."""
        url = reverse(
            "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name),
            args=[obj.pk],
        )
        return format_html(
            '<a class="button" href="{}" style="padding: 5px 10px; background-color: #417690; color: white; text-decoration: none; border-radius: 3px;">{}</a>',
            url,
            _("Edit"),
        )

    edit_button.short_description = _("Edit")
    edit_button.allow_tags = True

    def delete_button(self, obj: Subject) -> str:
        """Render a Delete button linking to the delete page for the object."""
        url = reverse(
            "admin:%s_%s_delete" % (obj._meta.app_label, obj._meta.model_name),
            args=[obj.pk],
        )
        return format_html(
            '<a class="button" href="{}" style="padding: 5px 10px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 3px;">{}</a>',
            url,
            _("Delete"),
        )

    delete_button.short_description = _("Delete")
    delete_button.allow_tags = True

    # ── Custom URLs ──

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:pk>/duplicate/",
                self.admin_site.admin_view(self.duplicate_view),
                name="curriculum_subject_duplicate",
            ),
        ]
        return custom + urls

    def duplicate_view(self, request, pk):
        obj = self.get_object(request, pk)
        if obj:
            obj.pk = None
            obj.slug = ""
            obj.name = f"{obj.name} (copy)"
            obj.save()
            self.message_user(
                request, _("Subject duplicated successfully."), messages.SUCCESS
            )
        return HttpResponseRedirect(reverse("admin:curriculum_subject_changelist"))

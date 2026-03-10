from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Specialty


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):

    list_display = (
        "short_name",
        "name",
        "grade",
        "level_display",
        "slug",
        "edit_button",
        "delete_button",
    )
    list_display_links = ("short_name",)
    list_filter = ("grade__level", "grade")
    search_fields = ("name", "short_name", "slug", "grade__name")
    ordering = ("grade__level__order", "grade__order", "name")
    list_per_page = 20
    list_max_show_all = 100
    readonly_fields = ("slug",)
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("grade",)

    fieldsets = (
        (
            _("General Information"),
            {
                "fields": ("grade", "name", "short_name", "slug"),
                "description": _(
                    "Specialty (filière) details. Only applicable to Secondaire grades."
                ),
            },
        ),
    )

    # ── Custom display methods ──

    @admin.display(description=_("Level"))
    def level_display(self, obj):
        return obj.grade.level.get_name_display()

    # ── Custom actions ──

    @admin.action(description=_("Reset slugs for selected specialties"))
    def reset_slugs(self, request, queryset):
        for obj in queryset:
            obj.slug = ""
            obj.save()
        self.message_user(
            request, _("Slugs have been reset and regenerated."), messages.SUCCESS
        )

    actions = ["reset_slugs"]

    def edit_button(self, obj: Specialty) -> str:
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

    def delete_button(self, obj: Specialty) -> str:
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


class SpecialtyInline(admin.TabularInline):
    model = Specialty
    extra = 0
    fields = ("name", "short_name", "slug")
    readonly_fields = ("slug",)
    show_change_link = True

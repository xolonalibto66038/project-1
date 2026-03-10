from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import Bookmark


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display = (
        "student",
        "target_type",
        "target_name_display",
        "object_id",
        "has_note",
        "created_at",
    )
    list_display_links = ("student",)
    list_filter = ("content_type", "created_at")
    search_fields = ("student__username", "student__email", "note", "object_id")
    ordering = ("-created_at",)
    list_per_page = 25
    list_max_show_all = 200

    # ── Detail view ──
    readonly_fields = (
        "content_object_display",
        "target_type",
        "created_at",
        "updated_at",
    )
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("student",)

    fieldsets = (
        (
            _("Who & What"),
            {
                "fields": (
                    "student",
                    "content_type",
                    "object_id",
                    "content_object_display",
                ),
                "description": _("The student and the bookmarked object."),
            },
        ),
        (
            _("Note"),
            {
                "fields": ("note",),
                "description": _("Optional personal note attached by the student."),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ── Custom display methods ──

    @admin.display(description=_("Type"))
    def target_type(self, obj):
        return obj.content_type.model if obj.content_type else "—"

    @admin.display(description=_("Target"))
    def target_name_display(self, obj):
        name = obj.target_name
        url = obj.target_url
        if url and url != "#":
            return format_html('<a href="{}" target="_blank">{}</a>', url, name)
        return name

    @admin.display(description=_("Has Note"), boolean=True)
    def has_note(self, obj):
        return bool(obj.note)

    @admin.display(description=_("Object"))
    def content_object_display(self, obj):
        target = obj.content_object
        if target is None:
            return format_html(
                '<span style="color:#dc3545;">Object no longer exists</span>'
            )
        name = getattr(target, "title", None) or getattr(target, "name", str(target))
        return format_html("<strong>{}</strong>: {}", obj.content_type.model, name)

    # ── Custom actions ──

    @admin.action(description=_("Delete selected bookmarks permanently"))
    def hard_delete(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, _(f"{count} bookmark(s) permanently deleted."), messages.WARNING
        )

    actions = ["hard_delete"]

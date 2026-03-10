from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..choices import InteractionType
from ..models import Interaction


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display = (
        "student",
        "interaction_badge",
        "target_type",
        "object_id",
        "created_at",
    )
    list_display_links = ("student",)
    list_filter = ("interaction_type", "content_type", "created_at")
    search_fields = ("student__username", "student__email", "object_id")
    ordering = ("-created_at",)
    list_per_page = 50
    list_max_show_all = 500

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

    # Interactions are audit data — no editing after creation
    def has_change_permission(self, request, obj=None):
        return False

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
                "description": _("The student and the object they interacted with."),
            },
        ),
        (
            _("Interaction"),
            {
                "fields": ("interaction_type",),
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

    @admin.display(description=_("Interaction"))
    def interaction_badge(self, obj):
        colors = {
            InteractionType.VIEW: "#007bff",
            InteractionType.DOWNLOAD: "#28a745",
            InteractionType.SHARE: "#6f42c1",
            InteractionType.SAVE: "#fd7e14",
        }
        icons = {
            InteractionType.VIEW: "👁",
            InteractionType.DOWNLOAD: "⬇",
            InteractionType.SHARE: "🔗",
            InteractionType.SAVE: "🔖",
        }
        color = colors.get(obj.interaction_type, "#6c757d")
        icon = icons.get(obj.interaction_type, "•")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; border-radius:4px;">'
            "{} {}</span>",
            color,
            icon,
            obj.get_interaction_type_display(),
        )

    @admin.display(description=_("Target Type"))
    def target_type(self, obj):
        return obj.content_type.model if obj.content_type else "—"

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

    @admin.action(description=_("Delete selected interactions permanently"))
    def hard_delete(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(
            request, _(f"{count} interaction(s) deleted."), messages.WARNING
        )

    actions = ["hard_delete"]

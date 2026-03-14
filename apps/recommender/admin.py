# recommendations/admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ItemFeatureVector


@admin.register(ItemFeatureVector)
class ItemFeatureVectorAdmin(admin.ModelAdmin):

    # ── List view ──────────────────────────────────────────────────────────────

    list_display = [
        "content_type",
        "object_id",
        "item_type",
        "difficulty",
        "term",
        "level_id",
        "grade_id",
        "subject_id",
        "specialty_id",
        "course_id",
        "last_synced_at",
    ]
    list_filter = [
        "content_type",
        "item_type",
        "difficulty",
        "term",
    ]
    search_fields = [
        "object_id",
        # UUIDs stored as strings — exact or startswith match
        "level_id",
        "grade_id",
        "subject_id",
        "specialty_id",
        "course_id",
    ]
    ordering = ["-last_synced_at"]

    # ── Detail view ────────────────────────────────────────────────────────────

    readonly_fields = [
        "content_type",
        "object_id",
        "content_object_link",
        "level_id",
        "grade_id",
        "subject_id",
        "specialty_id",
        "course_id",
        "last_synced_at",
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            _("Item"),
            {
                "fields": [
                    "content_type",
                    "object_id",
                    "content_object_link",
                ],
            },
        ),
        (
            _("Curriculum Hierarchy"),
            {
                "description": _(
                    "Cached FK values — populated automatically by signals. "
                    "Edit the source content object to change these."
                ),
                "fields": [
                    "level_id",
                    "grade_id",
                    "subject_id",
                    "specialty_id",
                    "course_id",
                ],
            },
        ),
        (
            _("Item Metadata"),
            {
                "fields": [
                    "item_type",
                    "difficulty",
                    "term",
                ],
            },
        ),
        (
            _("Housekeeping"),
            {
                "classes": ["collapse"],
                "fields": [
                    "last_synced_at",
                    "created_at",
                    "updated_at",
                ],
            },
        ),
    ]

    # ── Custom columns ─────────────────────────────────────────────────────────

    @admin.display(description=_("Source Object"))
    def content_object_link(self, obj):
        """
        Renders a link to the source object's admin change page.
        Falls back to the string representation when the object no longer exists.
        """
        from django.urls import NoReverseMatch, reverse
        from django.utils.html import format_html

        instance = obj.content_object
        if instance is None:
            return _("(deleted)")

        try:
            app_label = obj.content_type.app_label
            model_label = obj.content_type.model
            url = reverse(
                f"admin:{app_label}_{model_label}_change",
                args=[instance.pk],
            )
            return format_html('<a href="{}">{}</a>', url, instance)
        except NoReverseMatch:
            return str(instance)

    # ── Sync action ────────────────────────────────────────────────────────────

    actions = ["resync_vectors"]

    @admin.action(description=_("Re-sync selected feature vectors"))
    def resync_vectors(self, request, queryset):
        """
        Triggers a live re-extraction for each selected vector's source object.
        Useful after an extractor is updated and you want to backfill
        a handful of rows without running the full management command.
        """
        from .signals import _upsert_vector

        ok = errors = stale = 0

        for vector in queryset.select_related("content_type"):
            instance = vector.content_object
            if instance is None:
                stale += 1
                continue
            success = _upsert_vector(instance)
            if success:
                ok += 1
            else:
                errors += 1

        parts = [_(f"{ok} vector(s) re-synced successfully.")]
        if errors:
            parts.append(_(f"{errors} failed (check logs)."))
        if stale:
            parts.append(_(f"{stale} skipped — source object no longer exists."))

        self.message_user(request, "  ".join(str(p) for p in parts))

    # ── Permissions — vectors are managed by signals, not by hand ─────────────

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow editing item_type / difficulty / term for manual corrections
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

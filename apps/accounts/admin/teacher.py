# apps/accounts/admin/teacher_profile_admin.py

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import TeacherProfile


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display = (
        "full_name",
        "email_display",
        "level",
        "subject",
        "is_verified_teacher",
        "has_bio",
    )
    list_display_links = ("full_name",)
    list_filter = (
        "is_verified_teacher",
        "level",
        "subject",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "bio",
    )
    list_editable = ("is_verified_teacher",)
    ordering = ("user__last_name", "user__first_name")
    list_per_page = 25
    list_max_show_all = 200

    # ── Detail view ──
    readonly_fields = ("full_name", "email_display", "created_at", "updated_at")
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("user", "level", "subject")

    fieldsets = (
        (
            _("User Account"),
            {
                "fields": ("user", "full_name", "email_display"),
            },
        ),
        (
            _("Teaching Scope"),
            {
                "fields": ("level", "subject"),
                "description": _(
                    "A teacher is scoped to a Level + Subject. "
                    "The subject must belong to the selected level."
                ),
            },
        ),
        (
            _("Verification"),
            {
                "fields": ("is_verified_teacher",),
                "description": _("Only verified teachers can publish resources."),
            },
        ),
        (
            _("Profile"),
            {
                "fields": ("bio", "hour_price"),
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

    @admin.display(description=_("Full Name"))
    def full_name(self, obj):
        url = reverse("admin:accounts_customuser_change", args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())

    @admin.display(description=_("Email"))
    def email_display(self, obj):
        return obj.user.email

    @admin.display(description=_("Verified"))
    def verified_badge(self, obj):
        if obj.is_verified_teacher:
            return format_html(
                '<span style="background:#28a745; color:#fff; padding:2px 8px; '
                'border-radius:4px;">✓ Verified</span>'
            )
        return format_html(
            '<span style="background:#ffc107; color:#000; padding:2px 8px; '
            'border-radius:4px;">⏳ Pending</span>'
        )

    @admin.display(description=_("Bio"), boolean=True)
    def has_bio(self, obj):
        return bool(obj.bio)

    # ── Custom actions ──

    @admin.action(description=_("Verify selected teachers"))
    def verify_teachers(self, request, queryset):
        updated = queryset.update(is_verified_teacher=True)
        self.message_user(
            request,
            _(f"{updated} teacher(s) verified."),
            messages.SUCCESS,
        )

    @admin.action(description=_("Unverify selected teachers"))
    def unverify_teachers(self, request, queryset):
        updated = queryset.update(is_verified_teacher=False)
        self.message_user(
            request,
            _(f"{updated} teacher(s) unverified."),
            messages.WARNING,
        )

    actions = ["verify_teachers", "unverify_teachers"]

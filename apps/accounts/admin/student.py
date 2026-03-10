# apps/accounts/admin/student_profile_admin.py

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import StudentProfile


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):

    # ── List view ──
    list_display = (
        "full_name",
        "email_display",
        "grade",
        "level_display",
        "specialty",
        "has_bio",
    )
    list_display_links = ("full_name",)
    list_filter = (
        "grade__level",
        "grade",
        "specialty",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "bio",
    )
    ordering = ("user__last_name", "user__first_name")
    list_per_page = 25
    list_max_show_all = 200

    # ── Detail view ──
    readonly_fields = (
        "full_name",
        "email_display",
        "level_display",
        "created_at",
        "updated_at",
    )
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True
    autocomplete_fields = ("user", "grade", "specialty")

    fieldsets = (
        (
            _("User Account"),
            {
                "fields": ("user", "full_name", "email_display"),
            },
        ),
        (
            _("Academic Info"),
            {
                "fields": ("grade", "level_display", "specialty"),
                "description": _(
                    "Specialty is only applicable to Secondaire students."
                ),
            },
        ),
        (
            _("Profile"),
            {
                "fields": ("bio",),
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

    @admin.display(description=_("Level"))
    def level_display(self, obj):
        if not obj.grade:
            return "—"
        colors = {
            "primaire": "#28a745",
            "moyen": "#007bff",
            "secondaire": "#dc3545",
        }
        level = obj.grade.level
        color = colors.get(level.name, "#6c757d")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; '
            'border-radius:4px;">{}</span>',
            color,
            level.get_name_display(),
        )

    @admin.display(description=_("Bio"), boolean=True)
    def has_bio(self, obj):
        return bool(obj.bio)

    # ── Custom actions ──

    @admin.action(description=_("Clear specialty for selected students"))
    def clear_specialty(self, request, queryset):
        updated = queryset.update(specialty=None)
        self.message_user(
            request,
            _(f"{updated} student(s) specialty cleared."),
            messages.WARNING,
        )

    actions = ["clear_specialty"]

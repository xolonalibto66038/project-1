# apps/accounts/admin/custom_user_admin.py

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..choices import UserRole
from ..models import CustomUser, StudentProfile, TeacherProfile


class StudentProfileInline(admin.StackedInline):
    model = None  # set below after import
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name = _("Student Profile")
    fields = ("grade", "specialty", "bio")
    autocomplete_fields = ("grade", "specialty")


class TeacherProfileInline(admin.StackedInline):
    model = None  # set below after import
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name = _("Teacher Profile")
    fields = ("level", "subject", "bio", "is_verified_teacher", "hour_price")
    autocomplete_fields = ("level", "subject")


# Deferred imports to avoid circular
def get_inlines(obj):

    if obj and obj.role == UserRole.STUDENT:
        StudentProfileInline.model = StudentProfile
        return [StudentProfileInline]
    if obj and obj.role == UserRole.TEACHER:
        TeacherProfileInline.model = TeacherProfile
        return [TeacherProfileInline]
    return []


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    # ── List view ──
    list_display = (
        "avatar_display",
        "full_name_display",
        "email",
        "role_badge",
        "wilaya",
        "is_verified",
        "is_active",
        "date_joined",
    )
    list_display_links = ("avatar_display", "full_name_display")
    list_filter = (
        "role",
        "is_verified",
        "is_active",
        "is_staff",
        "gender",
        "wilaya",
        "date_joined",
    )
    search_fields = ("first_name", "last_name", "email", "phone")
    list_editable = ("is_verified", "is_active")
    ordering = ("-date_joined",)
    list_per_page = 25
    list_max_show_all = 200

    # ── Detail view ──
    readonly_fields = (
        "avatar_display",
        "date_joined",
        "last_login",
        "created_at",
        "updated_at",
    )
    save_on_top = True
    preserve_filters = True
    show_full_result_count = True

    # ── Override UserAdmin fieldsets (no username) ──
    fieldsets = (
        (
            _("Authentication"),
            {
                "fields": ("email", "password"),
            },
        ),
        (
            _("Personal Info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "gender",
                    "date_of_birth",
                    "phone",
                    "wilaya",
                    "avatar",
                    "avatar_display",
                ),
            },
        ),
        (
            _("Role & Verification"),
            {
                "fields": ("role", "is_verified"),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("date_joined", "last_login", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ── Add user fieldsets ──
    add_fieldsets = (
        (
            _("Required Info"),
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # ── Dynamic inlines based on role ──
    def get_inline_instances(self, request, obj=None):
        inlines = get_inlines(obj)
        return [inline(self.model, self.admin_site) for inline in inlines]

    # ── Custom display methods ──

    @admin.display(description=_("Avatar"))
    def avatar_display(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:36px; height:36px; '
                'border-radius:50%; object-fit:cover;"/>',
                obj.avatar.url,
            )
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper()
        return format_html(
            '<div style="width:36px; height:36px; border-radius:50%; '
            "background:#007bff; color:#fff; display:flex; "
            "align-items:center; justify-content:center; "
            'font-weight:bold; font-size:0.8em;">{}</div>',
            initials,
        )

    @admin.display(description=_("Full Name"))
    def full_name_display(self, obj):
        return obj.get_full_name()

    @admin.display(description=_("Role"))
    def role_badge(self, obj):
        colors = {
            UserRole.STUDENT: "#28a745",
            UserRole.TEACHER: "#007bff",
        }
        icons = {
            UserRole.STUDENT: "🎓",
            UserRole.TEACHER: "👨‍🏫",
        }
        color = colors.get(obj.role, "#6c757d")
        icon = icons.get(obj.role, "•")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 10px; '
            'border-radius:4px;">{} {}</span>',
            color,
            icon,
            obj.get_role_display(),
        )

    # ── Custom actions ──

    @admin.action(description=_("Verify selected users (email)"))
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, _(f"{updated} user(s) verified."), messages.SUCCESS)

    @admin.action(description=_("Unverify selected users"))
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(
            request, _(f"{updated} user(s) unverified."), messages.WARNING
        )

    @admin.action(description=_("Activate selected users"))
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f"{updated} user(s) activated."), messages.SUCCESS)

    @admin.action(description=_("Deactivate selected users"))
    def deactivate_users(self, request, queryset):
        updated = queryset.filter(is_superuser=False).update(is_active=False)
        self.message_user(
            request, _(f"{updated} user(s) deactivated."), messages.WARNING
        )

    actions = ["verify_users", "unverify_users", "activate_users", "deactivate_users"]

    # ── Custom URLs ──

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:pk>/impersonate/",
                self.admin_site.admin_view(self.impersonate_view),
                name="accounts_customuser_impersonate",
            ),
        ]
        return custom + urls

    def impersonate_view(self, request, pk):
        """Placeholder — wire to django-hijack or similar."""
        self.message_user(
            request,
            _("Impersonation requires django-hijack to be installed and configured."),
            messages.WARNING,
        )
        return HttpResponseRedirect(
            reverse("admin:accounts_customuser_change", args=[pk])
        )

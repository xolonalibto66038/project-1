from django.core.cache import cache
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from apps.accounts.choices import UserRole
from apps.accounts.models.custom_user import CustomUser
from apps.content.models.course import Course


class LandingPageView(TemplateView):
    template_name = "pages/landing.html"

    def dispatch(self, request, *args, **kwargs):
        # Authenticated users shouldn't see the landing page
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats = cache.get("landing_page_stats")
        if not stats:
            stats = {
                "courses_count": Course.objects.count(),
                "students_count": CustomUser.objects.filter(
                    role=UserRole.STUDENT
                ).count(),
                "teachers_count": CustomUser.objects.filter(
                    role=UserRole.TEACHER
                ).count(),
            }
            cache.set("landing_page_stats", stats, timeout=60 * 60)

        context.update(
            {
                "page_title": _("Welcome to EduGDZ"),
                "cta_text": _("Get Started"),
                **stats,
            }
        )
        return context

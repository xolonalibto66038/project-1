from django.urls import reverse
from django.views.generic import DetailView, ListView

from ..mixins import LevelQuerySetMixin
from ..models import Level
from ..selectors import get_grade_groups_with_specialties, get_level_stats

# ── config: one place to update level presentation ──
LEVEL_CONFIG = {
    "primaire": {
        "color": "primary",
        "image": "dist/img/levels/primary.png",
        "title": "Primary School",
        "description": "The foundation of a child's education, focusing on "
        "literacy, numeracy, and essential social values.",
    },
    "moyen": {
        "color": "info",
        "image": "dist/img/levels/middle.png",
        "title": "Middle School",
        "description": "A critical transitional phase that strengthens academic "
        "foundations and develops critical thinking.",
    },
    "secondaire": {
        "color": "warning",
        "image": "dist/img/levels/high.png",
        "title": "High School",
        "description": "Preparing students for higher education through "
        "specialised academic tracks.",
    },
    "university": {
        "color": "success",
        "image": "dist/img/levels/university.png",
        "title": "University",
        "description": "A hub for advanced learning, research, and innovation.",
    },
}


class LevelListView(LevelQuerySetMixin, ListView):
    template_name = "apps/curriculum/levels/list.html"
    context_object_name = "levels"

    # No pagination — levels are few and fixed (4 total)
    # If you ever have many levels, re-enable paginate_by

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        student_level = None

        if user.is_authenticated and getattr(user, "is_student", False):
            profile = getattr(user, "student_profile", None)
            if profile and profile.grade:
                student_level = profile.grade.level

        # ── Annotate each level with its presentation config ──
        enriched = []
        for level in context["levels"]:
            config = LEVEL_CONFIG.get(level.name, {})
            enriched.append(
                {
                    "level": level,
                    "color": config.get("color", "secondary"),
                    "image": config.get("image", "dist/img/levels/default.png"),
                    "title": config.get("title", level.get_name_display()),
                    "description": config.get("description", ""),
                    "is_student_level": student_level is not None
                    and level.pk == student_level.pk,
                }
            )

        context["enriched_levels"] = enriched
        context["crumbs"] = [
            {"label": "Home", "url": reverse("pages:landing"), "icon": "fas fa-home"},
            {"label": "Levels", "url": None},
        ]
        return context


class LevelDetailView(DetailView):
    model = Level
    template_name = "apps/curriculum/levels/detail.html"
    context_object_name = "level"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        student_grade = None

        if user.is_authenticated and getattr(user, "is_student", False):
            profile = getattr(user, "student_profile", None)
            student_grade = profile.grade

        level = self.object

        context["grade_groups"] = get_grade_groups_with_specialties(
            level, student_grade=student_grade
        )
        context["stats"] = get_level_stats(level)

        context["crumbs"] = [
            {"label": "Home", "url": reverse("pages:landing"), "icon": "fas fa-home"},
            {"label": "Levels", "url": reverse("curriculum:level:level-list")},
            {"label": level.get_name_display(), "url": None},
        ]

        return context

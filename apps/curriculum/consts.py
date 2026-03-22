from django.utils.translation import gettext_lazy as _

from apps.content.choices import ResourceType

# ── config: one place to update level presentation ──
LEVEL_CONFIG = {
    "primaire": {
        "color": "primary",
        "image": "dist/img/levels/primary.png",
        "title": "Primary School",
        "description": _(
            "The foundation of a child's education, focusing on "
            "literacy, numeracy, and essential social values."
        ),
    },
    "moyen": {
        "color": "info",
        "image": "dist/img/levels/middle.png",
        "title": "Middle School",
        "description": _(
            "A critical transitional phase that strengthens academic "
            "foundations and develops critical thinking."
        ),
    },
    "secondaire": {
        "color": "warning",
        "image": "dist/img/levels/high.png",
        "title": "High School",
        "description": _(
            "Preparing students for higher education through "
            "specialised academic tracks."
        ),
    },
    "university": {
        "color": "success",
        "image": "dist/img/levels/university.png",
        "title": "University",
        "description": _("A hub for advanced learning, research, and innovation."),
    },
}

SUBJECT_RESOURCE_TYPE_CONFIG = {
    "tests": {
        "resource_type": ResourceType.TEST,
        "tab": "tests",
        "title": _("Tests"),
        "icon": "fas fa-clipboard-check",
    },
    "exams": {
        "resource_type": ResourceType.EXAM,
        "tab": "exams",
        "title": _("Exams"),
        "icon": "fas fa-file-alt",
    },
    "past-papers": {
        "resource_type": ResourceType.PAST_PAPER,
        "tab": "past-papers",
        "title": _("Past Papers"),
        "icon": "fas fa-file-signature",
    },
    "mock-exams": {
        "resource_type": ResourceType.MOCK_EXAM,
        "tab": "mock-exams",
        "title": _("Mock Exams"),
        "icon": "fas fa-stopwatch",
    },
    "textbooks": {
        "resource_type": ResourceType.TEXTBOOK,
        "tab": "textbooks",
        "title": _("Textbooks"),
        "icon": "fas fa-book-open",
    },
    "foreign-books": {
        "resource_type": ResourceType.FOREIGN_BOOK,
        "tab": "foreign-books",
        "title": _("Foreign Books"),
        "icon": "fas fa-book",
    },
    "study-guides": {
        "resource_type": ResourceType.STUDY_GUIDE,
        "tab": "study-guides",
        "title": _("Study Guides"),
        "icon": "fas fa-book-reader",
    },
}

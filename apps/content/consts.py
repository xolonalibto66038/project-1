from django.utils.translation import gettext_lazy as _

from .choices import ResourceType

RESOURCE_TYPE_CONFIG = {
    "lessons": {
        "resource_type": ResourceType.LESSON,
        "tab": "lessons",
        "title": _("Lessons"),
        "icon": "fas fa-chalkboard-teacher",
    },
    "summaries": {
        "resource_type": ResourceType.SUMMARY,
        "tab": "summaries",
        "title": _("Summaries"),
        "icon": "fas fa-align-left",
    },
    "homeworks": {
        "resource_type": ResourceType.HOMEWORK,
        "tab": "homeworks",
        "title": _("Homeworks"),
        "icon": "fas fa-pencil-ruler",
    },
    "exercises": {
        "resource_type": ResourceType.EXERCISE,
        "tab": "exercises",
        "title": _("Exercises"),
        "icon": "fas fa-pencil-alt",
    },
    "notes": {
        "resource_type": ResourceType.NOTES,
        "tab": "notes",
        "title": _("Notes"),
        "icon": "fas fa-sticky-note",
    },
    "series": {
        "resource_type": ResourceType.SERIES,
        "tab": "series",
        "title": _("Series"),
        "icon": "fas fa-layer-group",
    },
}

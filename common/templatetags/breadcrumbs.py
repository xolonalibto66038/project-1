# apps/common/templatetags/breadcrumbs.py

from django import template

register = template.Library()


@register.inclusion_tag("includes/breadcrumb.html")
def breadcrumb(crumbs):
    """
    Usage: {% breadcrumb crumbs %}

    crumbs = [
        {"label": "Home", "url": "/", "icon": "fas fa-home"},
        {"label": "Levels", "url": "/levels/", "icon": None},
        {"label": "Maths", "url": None},  # last item — no url
    ]
    """
    return {"crumbs": crumbs}

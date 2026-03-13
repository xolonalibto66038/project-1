"""
Development settings.
Use: DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ── Database (SQLite for local dev) ──
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ── Email (print to console) ──
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── Debug toolbar (optional, install django-debug-toolbar) ──
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
# INTERNAL_IPS = ["127.0.0.1"]

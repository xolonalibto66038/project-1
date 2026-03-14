# config/settings/logging.py

from pathlib import Path

# ── Log directory ──────────────────────────────────────────────────────────────
# Creates  logs/  at the project root automatically if it doesn't exist.
# Add logs/ to your .gitignore.

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # ── Formatters ─────────────────────────────────────────────────────────────
    "formatters": {
        # RichHandler renders its own timestamp, level, and path —
        # keep the formatter minimal to avoid duplicating that information.
        "development_console": {
            "format": "%(name)s [%(request_id)s] — %(message)s",
            "datefmt": "%H:%M:%S",
        },
        # Plain text for files — no color codes, readable in any editor or tail.
        "development_file": {
            "format": "[{asctime}] {levelname:<8} {name} [{request_id}] — {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    # ── Filters ────────────────────────────────────────────────────────────────
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "request_id": {
            "()": "common.logging.filters.RequestIDFilter",
        },
    },
    # ── Handlers ───────────────────────────────────────────────────────────────
    "handlers": {
        # 1. Rich terminal — colored, beautiful tracebacks, dev only
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "development_console",
            "filters": ["require_debug_true", "request_id"],
            "level": "DEBUG",
            "rich_tracebacks": True,
            "tracebacks_show_locals": True,
            "show_time": True,
            "show_level": True,
            "show_path": True,
        },
        # 2. General activity — INFO and above
        "file_info": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "info.log"),
            "formatter": "development_file",
            "filters": ["request_id"],
            "level": "INFO",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
        # 3. Things needing attention — WARNING and above
        "file_warning": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "warning.log"),
            "formatter": "development_file",
            "filters": ["request_id"],
            "level": "WARNING",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
        # 4. Failures — ERROR and above, always has full tracebacks
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "error.log"),
            "formatter": "development_file",
            "filters": ["request_id"],
            "level": "ERROR",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
        # 5. SQL queries — isolated file, toggle level to DEBUG when needed
        "file_sql": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "sql.log"),
            "formatter": "development_file",
            "filters": ["request_id"],
            "level": "DEBUG",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB — SQL logs grow fast
            "backupCount": 3,
            "encoding": "utf-8",
        },
    },
    # ── Loggers ────────────────────────────────────────────────────────────────
    "loggers": {
        # ── Your app namespaces ────────────────────────────────────────────────
        "apps": {
            "handlers": ["console", "file_info", "file_warning", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
        "recommendations": {
            "handlers": ["console", "file_info", "file_warning", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
        "common": {
            "handlers": ["console", "file_info", "file_warning", "file_error"],
            "level": "DEBUG",
            "propagate": False,
        },
        # ── Django internals ───────────────────────────────────────────────────
        "django": {
            "handlers": ["console", "file_info", "file_warning", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            # Handles 4xx and 5xx — WARNING covers 4xx, ERROR covers 5xx
            "handlers": ["console", "file_warning", "file_error"],
            "level": "WARNING",
            "propagate": False,
        },
        # ── SQL queries ────────────────────────────────────────────────────────
        # Keep at WARNING normally — switch to DEBUG only when investigating
        # query issues, then switch back. sql.log stays empty otherwise.
        "django.db.backends": {
            "handlers": ["file_sql"],
            "level": "WARNING",
            "propagate": False,
        },
        # ── Third-party noise suppression ──────────────────────────────────────
        "PIL": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "boto3": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "botocore": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
    # ── Root logger ────────────────────────────────────────────────────────────
    # Safety net for any logger not explicitly configured above.
    "root": {
        "handlers": ["console", "file_warning", "file_error"],
        "level": "WARNING",
    },
}

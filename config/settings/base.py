"""
Base settings for config project.
Shared across all environments (development, staging, production).
"""

import os
from pathlib import Path

import cloudinary
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))

environ.Env.read_env(os.path.join(BASE_DIR, ".env.staging"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

X_FRAME_OPTIONS = "SAMEORIGIN"

AUTH_USER_MODEL = "accounts.CustomUser"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "cloudinary_storage",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # thirdparty apps
    "cloudinary",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "taggit",
    # internal apps
    "common",
    "apps.curriculum",
    "apps.content",
    "apps.feedback",
    "apps.progress",
    "apps.accounts",
    "apps.authentication",
    "apps.assessment",
    "apps.billing",
    "apps.tutoring",
]

SITE_ID = 1

DOMAIN = env("DOMAIN", default="http://localhost:8000")

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # thirdparty
    "allauth.account.middleware.AccountMiddleware",
    # internal
    "apps.authentication.middleware.OnboardingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# Use plain static files storage
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
# STORAGES = {
#     "default": {
#         "BACKEND": "django.core.files.storage.FileSystemStorage",
#     },
#     "staticfiles": {
#         "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#     },
# }

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── allauth core ──
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "first_name*",
    "last_name*",
    "password1*",
    "password2*",
]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[EduGDZ] "
ACCOUNT_MAX_EMAIL_ADDRESSES = 2
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# ── redirects ──
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "/dashboard/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# ── adapter ──
ACCOUNT_ADAPTER = "apps.authentication.adapters.CustomAccountAdapter"
SOCIALACCOUNT_ADAPTER = "apps.authentication.adapters.CustomSocialAccountAdapter"

# ── forms ──
ACCOUNT_FORMS = {
    "signup": "apps.authentication.forms.CustomSignupForm",
    "login": "apps.authentication.forms.CustomLoginForm",
    "reset_password": "apps.authentication.forms.CustomResetPasswordForm",
    "change_password": "apps.authentication.forms.CustomChangePasswordForm",
}

# ── social ──
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_CLIENT_ID", default=""),
            "secret": env("GOOGLE_CLIENT_SECRET", default=""),
        },
        "SCOPE": ["profile", "email"],
        "FETCH_USERINFO": True,
        "AUTH_PARAMS": {"access_type": "online", "prompt": "select_account"},
        "OAUTH_PKCE_ENABLED": True,
    }
}

CONTACT_EMAIL = env("CONTACT_EMAIL", default="xolonalibto66038@gmail.com")

# ── Stripe ──
STRIPE_TEST_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_ENDPOINT_SECRET = env("STRIPE_ENDPOINT_SECRET", default="")
PLATFORM_FEE_PERCENT = env("PLATFORM_FEE_PERCENT", default="20")
STRIPE_CURRENCY = env("STRIPE_CURRENCY", default="usd")

# ── Zoom ──
ZOOM_ACCOUNT_ID = env("ZOOM_ACCOUNT_ID", default="")
ZOOM_CLIENT_ID = env("ZOOM_CLIENT_ID", default="")
ZOOM_CLIENT_SECRET = env("ZOOM_CLIENT_SECRET", default="")
ZOOM_BASE_URL = env("ZOOM_BASE_URL", default="")
ZOMM_SECRET_TOKEN = env("ZOMM_SECRET_TOKEN", default="")
ZOOM_WEBHOOK_SECRET = env("ZOOM_WEBHOOK_SECRET", default="")
ZOOM_HOST_EMAIL = env("ZOOM_HOST_EMAIL", default="")

# ── Google Meet / Calendar ──
GOOGLE_SERVICE_ACCOUNT_FILE = env("GOOGLE_SERVICE_ACCOUNT_FILE", default="")
GOOGLE_CALENDAR_HOST_EMAIL = env("GOOGLE_CALENDAR_HOST_EMAIL", default="")

from django.urls import include, path

from .views import (
    DashboardView,
    OnboardingView,
    SocialRoleSelectView,
    load_specialties,
    load_subjects,
)

# app_name = 'authentication'


urlpatterns = [
    path(
        "accounts/social/role/",
        SocialRoleSelectView.as_view(),
        name="social_role_select",
    ),
    path("onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("ajax/specialties/", load_specialties, name="ajax_specialties"),
    path("ajax/subjects/", load_subjects, name="ajax_subjects"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("allauth.socialaccount.urls")),
]

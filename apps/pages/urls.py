from django.urls import path

from .views import (
    AboutUsPageView,
    ContactUsView,
    FAQPageView,
    LandingPageView,
    PrivacyPageView,
    TermsPageView,
)

app_name = "pages"

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path("contact_us/", ContactUsView.as_view(), name="contact-us"),
    path("about_us/", AboutUsPageView.as_view(), name="about-us"),
    path("faq/", FAQPageView.as_view(), name="faq"),
    path("privacy/", PrivacyPageView.as_view(), name="privacy"),
    path("terms/", TermsPageView.as_view(), name="terms"),
]

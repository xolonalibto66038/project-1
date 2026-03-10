from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView


class PrivacyPageView(TemplateView):
    template_name = "pages/privacy.html"

    SECTIONS = [
        {
            "id": "information-we-collect",
            "icon": "fas fa-database",
            "color": "primary",
            "title": _("Information We Collect"),
            "content": [
                _(
                    "Account information: name, email address, and role (student or teacher) provided during registration."
                ),
                _(
                    "Profile information: grade, specialty, level, or subject depending on your role."
                ),
                _(
                    "Usage data: pages visited, resources accessed, quizzes taken, and progress tracked."
                ),
                _(
                    "Device information: browser type, IP address, and operating system for security purposes."
                ),
                _("Communications: messages sent through the contact form."),
            ],
        },
        {
            "id": "how-we-use",
            "icon": "fas fa-cogs",
            "color": "info",
            "title": _("How We Use Your Information"),
            "content": [
                _("To provide, maintain, and improve the EduGDZ platform."),
                _(
                    "To personalise your learning experience based on your grade, level, and progress."
                ),
                _(
                    "To communicate with you about your account, updates, or support requests."
                ),
                _("To monitor platform usage and detect security issues."),
                _("To comply with legal obligations."),
            ],
        },
        {
            "id": "data-sharing",
            "icon": "fas fa-share-alt",
            "color": "warning",
            "title": _("Data Sharing"),
            "content": [
                _(
                    "We do not sell, rent, or trade your personal data to third parties."
                ),
                _(
                    "We may share data with trusted service providers who assist us in operating the platform, under strict confidentiality agreements."
                ),
                _(
                    "We may disclose information if required by law or to protect the rights and safety of our users."
                ),
                _(
                    "Aggregated, anonymised statistics may be shared publicly (e.g. total number of students)."
                ),
            ],
        },
        {
            "id": "data-retention",
            "icon": "fas fa-clock",
            "color": "secondary",
            "title": _("Data Retention"),
            "content": [
                _("We retain your account data for as long as your account is active."),
                _(
                    "If you delete your account, your personal data will be permanently removed within 30 days."
                ),
                _(
                    "Anonymised usage data may be retained indefinitely for analytical purposes."
                ),
                _("Contact form submissions are retained for up to 12 months."),
            ],
        },
        {
            "id": "your-rights",
            "icon": "fas fa-user-shield",
            "color": "success",
            "title": _("Your Rights"),
            "content": [
                _(
                    "Access: you may request a copy of the personal data we hold about you."
                ),
                _(
                    "Correction: you may update or correct your information at any time from your profile settings."
                ),
                _(
                    "Deletion: you may request deletion of your account and associated data."
                ),
                _("Objection: you may object to certain types of data processing."),
                _(
                    "Portability: you may request your data in a machine-readable format."
                ),
            ],
        },
        {
            "id": "cookies",
            "icon": "fas fa-cookie-bite",
            "color": "danger",
            "title": _("Cookies"),
            "content": [
                _("We use session cookies to keep you logged in during your visit."),
                _("We use preference cookies to remember your settings."),
                _("We do not use advertising or tracking cookies."),
                _(
                    "You can disable cookies in your browser settings, but some features may not function correctly."
                ),
            ],
        },
        {
            "id": "security",
            "icon": "fas fa-lock",
            "color": "dark",
            "title": _("Security"),
            "content": [
                _("All data is transmitted over HTTPS using TLS encryption."),
                _(
                    "Passwords are hashed using industry-standard algorithms and are never stored in plain text."
                ),
                _(
                    "We regularly review our security practices and apply updates promptly."
                ),
                _(
                    "Despite our efforts, no method of transmission over the internet is 100% secure."
                ),
            ],
        },
        {
            "id": "third-party",
            "icon": "fas fa-external-link-alt",
            "color": "info",
            "title": _("Third-Party Services"),
            "content": [
                _(
                    "We use Google OAuth for social login. Google's privacy policy applies to data processed by Google."
                ),
                _(
                    "We may embed YouTube videos. YouTube's privacy policy applies when videos are played."
                ),
                _("We do not use third-party advertising networks."),
            ],
        },
        {
            "id": "children",
            "icon": "fas fa-child",
            "color": "warning",
            "title": _("Children's Privacy"),
            "content": [
                _(
                    "EduGDZ is intended for use by students of all ages within the Algerian education system."
                ),
                _(
                    "For users under 13, we recommend parental supervision during registration."
                ),
                _(
                    "We do not knowingly collect personal data from children under 13 without parental consent."
                ),
                _(
                    "If you believe a child has provided us data without consent, please contact us immediately."
                ),
            ],
        },
        {
            "id": "changes",
            "icon": "fas fa-edit",
            "color": "secondary",
            "title": _("Changes to This Policy"),
            "content": [
                _("We may update this Privacy Policy from time to time."),
                _(
                    "We will notify registered users of significant changes via email or an in-app notification."
                ),
                _(
                    "Continued use of the platform after changes constitutes acceptance of the updated policy."
                ),
                _(
                    'The "Last Updated" date at the top of this page reflects the most recent revision.'
                ),
            ],
        },
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Privacy Policy"),
                "page_subtitle": _("How we collect, use, and protect your data"),
                "last_updated": "1 January 2026",
                "sections": self.SECTIONS,
                "contact_email": settings.CONTACT_EMAIL,
            }
        )
        return context

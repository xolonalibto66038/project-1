from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView


class FAQPageView(TemplateView):
    template_name = "pages/faq.html"

    # ── Keep FAQs in the view — easy to move to DB later ──
    FAQS = [
        {
            "id": "faq1",
            "icon": "fas fa-info-circle",
            "color": "primary",
            "question": _("Is EduGDZ free to use?"),
            "answer": _(
                "Yes. EduGDZ is completely free. All educational resources can be accessed without any fees or subscriptions."
            ),
        },
        {
            "id": "faq2",
            "icon": "fas fa-download",
            "color": "warning",
            "question": _("Can I download study materials?"),
            "answer": _(
                "Some materials are available for download depending on resource type and permissions. Not all content is downloadable."
            ),
        },
        {
            "id": "faq3",
            "icon": "fas fa-folder-open",
            "color": "danger",
            "question": _("Can I download all topics in one file?"),
            "answer": _(
                "No. Topics are managed individually to ensure accurate updates and better organization."
            ),
        },
        {
            "id": "faq4",
            "icon": "fas fa-bug",
            "color": "info",
            "question": _("Why do some topics contain errors?"),
            "answer": _(
                "While we strive for accuracy, errors may occasionally occur. Please report any issues through the contact page."
            ),
        },
        {
            "id": "faq5",
            "icon": "fas fa-certificate",
            "color": "success",
            "question": _("Does EduGDZ provide certificates?"),
            "answer": _(
                "No. EduGDZ focuses on educational support and exam preparation materials, not formal certification."
            ),
        },
        {
            "id": "faq6",
            "icon": "fas fa-envelope",
            "color": "secondary",
            "question": _("How can I get help with a specific topic?"),
            "answer": _(
                "You can ask in the topic discussion section or contact us through the contact form."
            ),
        },
        {
            "id": "faq7",
            "icon": "fas fa-share-alt",
            "color": "dark",
            "question": _("Can EduGDZ content be shared elsewhere?"),
            "answer": _(
                "Content may be shared for educational, non-commercial purposes only. Commercial use without permission is prohibited."
            ),
        },
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_title": _("Frequently Asked Questions"),
                "page_subtitle": _(
                    "Find clear answers to the most common questions about EduGDZ"
                ),
                "faqs": self.FAQS,
            }
        )
        return context

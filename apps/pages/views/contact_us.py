from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from ..forms import ContactForm


class ContactUsView(FormView):
    template_name = "pages/contact-us.html"
    form_class = ContactForm
    success_url = reverse_lazy("pages:contact")

    def form_valid(self, form):
        try:
            form.save()
            messages.success(
                self.request,
                _("Your message has been sent. We'll get back to you shortly."),
            )
        except Exception:
            messages.error(
                self.request,
                _("Something went wrong on our end. Please try again later."),
            )
            return self.form_invalid(form)
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            _("Please correct the errors below and try again."),
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Contact Us")
        ctx["page_subtitle"] = _("We'd love to hear from you")
        return ctx

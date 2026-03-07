from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _


class AboutUsPageView(TemplateView):
    template_name = 'pages/about-us.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title':    _('About Us'),
            'page_subtitle': _('Who we are and why we built this platform'),
            'cta_text':      _('Get Started'),
        })
        return context
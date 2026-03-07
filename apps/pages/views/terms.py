from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class TermsPageView(TemplateView):
    template_name = 'pages/terms.html'

    SECTIONS = [
        {
            'id':      'acceptance',
            'icon':    'fas fa-handshake',
            'color':   'primary',
            'title':   _('Acceptance of Terms'),
            'content': [
                _('By accessing or using EduGDZ, you confirm that you have read, understood, and agree to be bound by these Terms of Service.'),
                _('If you do not agree with any part of these terms, you must not use the platform.'),
                _('These terms apply to all users including students, teachers, and guests.'),
                _('We reserve the right to update these terms at any time. Continued use after changes constitutes acceptance.'),
            ],
        },
        {
            'id':      'eligibility',
            'icon':    'fas fa-user-check',
            'color':   'info',
            'title':   _('Eligibility'),
            'content': [
                _('EduGDZ is designed for students and teachers within the Algerian education system.'),
                _('You must provide accurate and complete information during registration.'),
                _('Users under 13 years of age require parental or guardian consent to register.'),
                _('EduGDZ reserves the right to refuse service to anyone at its sole discretion.'),
            ],
        },
        {
            'id':      'accounts',
            'icon':    'fas fa-user-circle',
            'color':   'warning',
            'title':   _('User Accounts'),
            'content': [
                _('You are responsible for maintaining the confidentiality of your account credentials.'),
                _('You are fully responsible for all activity that occurs under your account.'),
                _('You must notify us immediately of any unauthorised use of your account.'),
                _('You may not share your account with others or create multiple accounts for the same person.'),
                _('We reserve the right to suspend or terminate accounts that violate these terms.'),
            ],
        },
        {
            'id':      'acceptable-use',
            'icon':    'fas fa-thumbs-up',
            'color':   'success',
            'title':   _('Acceptable Use'),
            'content': [
                _('You agree to use EduGDZ only for lawful educational purposes.'),
                _('You must not upload, share, or distribute content that is offensive, harmful, or violates any law.'),
                _('You must not attempt to gain unauthorised access to any part of the platform or its systems.'),
                _('You must not use the platform to spam, harass, or impersonate other users.'),
                _('You must not use automated tools, bots, or scrapers to access platform content without permission.'),
                _('Violations may result in immediate account suspension without prior notice.'),
            ],
        },
        {
            'id':      'content-ownership',
            'icon':    'fas fa-copyright',
            'color':   'danger',
            'title':   _('Content & Intellectual Property'),
            'content': [
                _('All content on EduGDZ — including lessons, exercises, exams, and platform design — is the intellectual property of EduGDZ or its content contributors.'),
                _('You may not reproduce, distribute, or commercially exploit any platform content without explicit written permission.'),
                _('Teachers who upload content to EduGDZ grant EduGDZ a non-exclusive licence to display and distribute that content to students.'),
                _('You retain ownership of content you create, but you are responsible for ensuring it does not infringe on third-party rights.'),
                _('Content that violates copyright or intellectual property laws will be removed without notice.'),
            ],
        },
        {
            'id':      'teacher-responsibilities',
            'icon':    'fas fa-chalkboard-teacher',
            'color':   'info',
            'title':   _('Teacher Responsibilities'),
            'content': [
                _('Teachers are responsible for the accuracy and quality of the content they upload.'),
                _('Teachers must ensure that uploaded content complies with the Algerian national curriculum where applicable.'),
                _('Teachers must not upload content that infringes on third-party intellectual property.'),
                _('Verified teacher status may be revoked if content standards are repeatedly violated.'),
                _('Teachers are responsible for maintaining professional conduct in all interactions with students on the platform.'),
            ],
        },
        {
            'id':      'student-responsibilities',
            'icon':    'fas fa-user-graduate',
            'color':   'success',
            'title':   _('Student Responsibilities'),
            'content': [
                _('Students must use the platform in good faith for genuine learning purposes.'),
                _('Students must not share quiz answers, cheat on assessments, or engage in academic dishonesty.'),
                _('Students must treat teachers and other users with respect.'),
                _('Students are responsible for their own learning progress and engagement with the platform.'),
            ],
        },
        {
            'id':      'disclaimers',
            'icon':    'fas fa-exclamation-triangle',
            'color':   'warning',
            'title':   _('Disclaimers'),
            'content': [
                _('EduGDZ is provided "as is" without warranties of any kind, express or implied.'),
                _('We do not guarantee that the platform will be error-free, uninterrupted, or meet your specific requirements.'),
                _('We are not responsible for the accuracy of content uploaded by third-party teachers.'),
                _('EduGDZ does not issue official diplomas, certificates, or qualifications recognised by the Algerian Ministry of Education.'),
                _('We are not liable for any loss of data, interruption of service, or damages arising from platform use.'),
            ],
        },
        {
            'id':      'termination',
            'icon':    'fas fa-ban',
            'color':   'danger',
            'title':   _('Termination'),
            'content': [
                _('You may delete your account at any time from your profile settings.'),
                _('We reserve the right to suspend or permanently terminate your account for violations of these terms.'),
                _('Upon termination, your access to the platform will be revoked immediately.'),
                _('Content you have uploaded may be retained or removed at our discretion following termination.'),
                _('Provisions of these terms that by their nature should survive termination will remain in effect.'),
            ],
        },
        {
            'id':      'governing-law',
            'icon':    'fas fa-gavel',
            'color':   'secondary',
            'title':   _('Governing Law'),
            'content': [
                _('These Terms of Service are governed by the laws of the People\'s Democratic Republic of Algeria.'),
                _('Any disputes arising from these terms shall be subject to the exclusive jurisdiction of Algerian courts.'),
                _('If any provision of these terms is found to be unenforceable, the remaining provisions will continue in full effect.'),
            ],
        },
        {
            'id':      'contact',
            'icon':    'fas fa-envelope',
            'color':   'primary',
            'title':   _('Contact'),
            'content': [
                _('If you have questions about these Terms of Service, please contact us via the contact form or by email.'),
                _('We will respond to all legal enquiries within 5 business days.'),
            ],
        },
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title':    _('Terms of Service'),
            'page_subtitle': _('Please read these terms carefully before using EduGDZ'),
            'last_updated':  '1 January 2026',
            'sections':      self.SECTIONS,
            'contact_email': settings.CONTACT_EMAIL,
        })
        return context
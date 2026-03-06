# apps/authentication/views.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.generic import TemplateView

from apps.accounts.choices import UserRole
from apps.curriculum.models import Specialty, Subject

from .forms import StudentOnboardingForm, TeacherOnboardingForm


class OnboardingView(LoginRequiredMixin, FormView):
    """
    Post-signup onboarding step.
    Collects grade/specialty for students, level/subject for teachers.
    Redirects to dashboard on completion.
    """

    template_name = 'account/onboarding.html'
    success_url   = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        # Already onboarded — skip
        if request.user.is_authenticated and self._is_complete(request.user):
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        if self.request.user.role == UserRole.STUDENT:
            return StudentOnboardingForm
        return TeacherOnboardingForm

    def get_template_names(self):
        if self.request.user.role == UserRole.STUDENT:
            return ['account/onboarding_student.html']
        return ['account/onboarding_teacher.html']

    def form_valid(self, form):
        user = self.request.user
        if user.role == UserRole.STUDENT:
            self._save_student(user, form)
        elif user.role == UserRole.TEACHER:
            self._save_teacher(user, form)
        return super().form_valid(form)

    def _save_student(self, user, form):
        profile          = user.student_profile
        profile.grade    = form.cleaned_data['grade']
        profile.specialty = form.cleaned_data.get('specialty')
        profile.save()

    def _save_teacher(self, user, form):
        profile         = user.teacher_profile
        profile.level   = form.cleaned_data['level']
        profile.subject = form.cleaned_data['subject']
        profile.save()

    def _is_complete(self, user):
        if user.is_student:
            profile = getattr(user, 'student_profile', None)
            return profile and profile.grade is not None
        if user.is_teacher:
            profile = getattr(user, 'teacher_profile', None)
            return profile and profile.level is not None and profile.subject is not None
        return True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['user'] = self.request.user
        return ctx


# ── AJAX endpoints for dynamic dropdowns ──

def load_specialties(request):
    """Returns specialties for a given grade — called via AJAX."""
    grade_id    = request.GET.get('grade_id')
    specialties = Specialty.objects.filter(
        grade_id=grade_id
    ).order_by('name').values('id', 'name')
    return JsonResponse({'specialties': list(specialties)})


def load_subjects(request):
    """Returns subjects for a given level — called via AJAX."""
    level_id = request.GET.get('level_id')
    subjects = Subject.objects.filter(
        level_id=level_id
    ).order_by('name').values('id', 'name')
    return JsonResponse({'subjects': list(subjects)})


class DashboardView(LoginRequiredMixin, TemplateView):

    def get_template_names(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return ['dashboard/admin.html']
        if user.is_student:
            return ['dashboard/student.html']
        if user.is_teacher:
            return ['dashboard/teacher.html']
        return ['dashboard/base.html']

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['user'] = user

        if user.is_student:
            profile = getattr(user, 'student_profile', None)
            ctx['profile']  = profile
            ctx['grade']    = profile.grade if profile else None
            ctx['level']    = profile.level if profile else None
            ctx['specialty'] = profile.specialty if profile else None

        elif user.is_teacher:
            profile = getattr(user, 'teacher_profile', None)
            ctx['profile'] = profile
            ctx['level']   = profile.level if profile else None
            ctx['subject'] = profile.subject if profile else None

        return ctx
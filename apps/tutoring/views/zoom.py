# apps/tutoring/views/zoom_views.py

import logging

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView

from apps.authentication.mixins import StudentRequiredMixin, TeacherRequiredMixin
from apps.billing.services import StripeService

from ..models import ZoomSession
from ..services.zoom import ZoomService

logger = logging.getLogger(__name__)


# ── Teacher Views ──────────────────────────────────────────────────────────────


class TeacherZoomSessionsView(TeacherRequiredMixin, ListView):
    template_name = "apps/tutoring/teacher/zoom_sessions.html"
    context_object_name = "sessions"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            ZoomSession.objects.filter(teacher=self.request.user)
            .select_related("student__student_profile")
            .order_by("-created_at")
        )

        state = self.request.GET.get("state", "").strip()
        if state and state in ZoomSession.State.values:
            qs = qs.filter(state=state)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qp = self.request.GET.copy()
        qp.pop("page", None)

        context.update(
            {
                "state_choices": ZoomSession.State.choices,
                "filter_state": self.request.GET.get("state", ""),
                "querystring": qp.urlencode(),
                "state_counts": (
                    ZoomSession.objects.filter(teacher=self.request.user)
                    .values("state")
                    .annotate(count=Count("id"))
                ),
            }
        )

        return context


class TeacherZoomSessionDetailView(TeacherRequiredMixin, DetailView):
    template_name = "apps/tutoring/teacher/zoom_session_detail.html"
    context_object_name = "session"
    pk_url_kwarg = "session_id"

    def get_queryset(self):
        return ZoomSession.objects.filter(teacher=self.request.user).select_related(
            "student__student_profile",
            "teacher__teacher_profile",
        )


class TeacherAcceptZoomSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            ZoomSession,
            pk=session_id,
            teacher=request.user,
            state=ZoomSession.State.PENDING_TEACHER,
        )
        try:
            ZoomService.teacher_accept(session)
            messages.success(
                request, _("Session accepted. Student will be notified to pay.")
            )
        except Exception:
            logger.exception("teacher_accept failed for session %s", session_id)
            messages.error(request, _("Unable to accept session. Please try again."))

        return redirect(
            reverse(
                "tutoring:zoom:zoom-session-detail",
                kwargs={"session_id": session_id},
            )
        )


class TeacherRejectZoomSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            ZoomSession,
            pk=session_id,
            teacher=request.user,
            state=ZoomSession.State.PENDING_TEACHER,
        )
        reason = request.POST.get("reason", "").strip()
        try:
            ZoomService.teacher_reject(session, reason=reason)
            messages.success(request, _("Session rejected."))
        except Exception:
            logger.exception("teacher_reject failed for session %s", session_id)
            messages.error(request, _("Unable to reject session. Please try again."))

        return redirect(reverse("tutoring:zoom:zoom-sessions"))


class TeacherStartZoomSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            ZoomSession,
            pk=session_id,
            teacher=request.user,
            state=ZoomSession.State.CONFIRMED,
        )
        try:
            ZoomService.start_session(session)
            messages.success(request, _("Session started."))
        except Exception:
            logger.exception("start_session failed for session %s", session_id)
            messages.error(request, _("Unable to start session."))

        return redirect(
            reverse(
                "tutoring:zoom:zoom-session-detail",
                kwargs={"session_id": session_id},
            )
        )


class TeacherCompleteZoomSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            ZoomSession,
            pk=session_id,
            teacher=request.user,
            state=ZoomSession.State.IN_PROGRESS,
        )
        try:
            ZoomService.complete_session(session)
            messages.success(request, _("Session marked as completed."))
        except Exception:
            logger.exception("complete_session failed for session %s", session_id)
            messages.error(request, _("Unable to complete session."))

        return redirect(
            reverse(
                "tutoring:zoom:zoom-session-detail",
                kwargs={"session_id": session_id},
            )
        )


class TeacherCancelZoomSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            ZoomSession,
            pk=session_id,
            teacher=request.user,
            state__in=[
                ZoomSession.State.PENDING_TEACHER,
                ZoomSession.State.PENDING_PAYMENT,
                ZoomSession.State.CONFIRMED,
            ],
        )
        reason = request.POST.get("reason", "").strip()
        try:
            ZoomService.cancel_session(session, actor=request.user, reason=reason)
            messages.success(request, _("Session cancelled."))
        except Exception:
            logger.exception("cancel_session failed for session %s", session_id)
            messages.error(request, _("Unable to cancel session."))

        return redirect(reverse("tutoring:zoom:zoom-sessions"))


# ── Student Views ──────────────────────────────────────────────────────────────


class StudentZoomSessionsView(StudentRequiredMixin, ListView):
    template_name = "apps/tutoring/student/zoom_sessions.html"
    context_object_name = "sessions"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            ZoomSession.objects.filter(student=self.request.user)
            .select_related("teacher__teacher_profile")
            .order_by("-created_at")
        )

        state = self.request.GET.get("state", "").strip()
        if state and state in ZoomSession.State.values:
            qs = qs.filter(state=state)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qp = self.request.GET.copy()
        qp.pop("page", None)

        context.update(
            {
                "state_choices": ZoomSession.State.choices,
                "filter_state": self.request.GET.get("state", ""),
                "querystring": qp.urlencode(),
                "state_counts": (
                    ZoomSession.objects.filter(student=self.request.user)
                    .values("state")
                    .annotate(count=Count("id"))
                ),
            }
        )

        return context


class StudentZoomSessionDetailView(StudentRequiredMixin, DetailView):
    template_name = "apps/tutoring/student/zoom_session_detail.html"
    context_object_name = "session"
    pk_url_kwarg = "session_id"

    def get_queryset(self):
        return ZoomSession.objects.filter(student=self.request.user).select_related(
            "teacher__teacher_profile",
            "student__student_profile",
        )


class StudentCancelZoomSessionView(StudentRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            ZoomSession,
            pk=session_id,
            student=request.user,
            state__in=[
                ZoomSession.State.PENDING_TEACHER,
                ZoomSession.State.PENDING_PAYMENT,
            ],
        )
        reason = request.POST.get("reason", "").strip()
        try:
            ZoomService.cancel_session(session, actor=request.user, reason=reason)
            messages.success(request, _("Session cancelled successfully."))
        except Exception:
            logger.exception("student cancel_session failed for session %s", session_id)
            messages.error(request, _("Unable to cancel session. Please try again."))

        return redirect(reverse("tutoring:zoom:student-zoom-sessions"))


class StudentZoomSessionPayView(StudentRequiredMixin, View):

    def get(self, request, session_id):
        session = get_object_or_404(
            ZoomSession,
            pk=session_id,
            student=request.user,
            state=ZoomSession.State.PENDING_PAYMENT,
        )

        try:
            checkout = StripeService.create_zoom_checkout_session(
                student=request.user,
                session=session,
            )

            if not checkout:
                raise Exception("Stripe checkout creation failed.")

            return redirect(checkout.url)

        except Exception as ex:
            logger.exception("zoom session pay failed: %s", str(ex))
            messages.error(request, _("Unable to initiate payment. Please try again."))
            return redirect(
                reverse(
                    "tutoring:zoom:student-zoom-session-detail",
                    kwargs={"session_id": session_id},
                )
            )

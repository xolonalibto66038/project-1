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

from ..models import GoogleSession
from ..services.meet import MeetService

logger = logging.getLogger(__name__)

# class GoogleSessionViewSet(ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     queryset = GoogleSession.objects.select_related("student", "teacher", "payment")

#     def get_queryset(self):
#         user = self.request.user
#         return self.queryset.filter(models.Q(student=user) | models.Q(teacher=user))

#     # POST /sessions/request/
#     @action(detail=False, methods=["post"])
#     def request(self, request):
#         s = request.data
#         session = MeetService.request_session(
#             student=request.user,
#             teacher_id=s["teacher_id"],
#             proposed_start=s["proposed_start"],
#             proposed_end=s["proposed_end"],
#             notes=s.get("notes", ""),
#         )
#         return Response({"session_id": session.pk, "state": session.state}, status=201)

#     # POST /sessions/{pk}/accept/   (teacher only)
#     @action(detail=True, methods=["post"])
#     def accept(self, request, pk=None):
#         session = self.get_object()
#         if request.user != session.teacher:
#             return Response({"detail": "Only the teacher can accept."}, status=403)
#         MeetService.teacher_accept(session)
#         return Response({"state": session.state})

#     # POST /sessions/{pk}/reject/   (teacher only)
#     @action(detail=True, methods=["post"])
#     def reject(self, request, pk=None):
#         session = self.get_object()
#         if request.user != session.teacher:
#             return Response({"detail": "Only the teacher can reject."}, status=403)
#         MeetService.teacher_reject(session, reason=request.data.get("reason", ""))
#         return Response({"state": session.state})

#     # POST /sessions/{pk}/start/   (teacher only — opens the meeting)
#     @action(detail=True, methods=["post"])
#     def start(self, request, pk=None):
#         session = self.get_object()
#         if request.user != session.teacher:
#             return Response(
#                 {"detail": "Only the teacher can start the meeting."}, status=403
#             )
#         MeetService.start_session(session)
#         return Response(
#             {
#                 "state": session.state,
#                 "meet_link": session.google_meet_link,
#             }
#         )

#     # GET /sessions/{pk}/join/   (student — returns Meet link after validating join code)
#     @action(detail=True, methods=["get"])
#     def join(self, request, pk=None):
#         session = self.get_object()
#         if request.user != session.student:
#             return Response({"detail": "Forbidden."}, status=403)
#         if session.state not in (
#             GoogleSession.State.PAID,
#             GoogleSession.State.ACTIVE,
#         ):
#             return Response({"detail": "Session is not ready to join."}, status=400)
#         code = request.query_params.get("code", "")
#         if session.join_code and code != session.join_code:
#             return Response({"detail": "Invalid join code."}, status=403)
#         return Response(
#             {
#                 "meet_link": session.google_meet_link,
#                 "state": session.state,
#             }
#         )

#     # POST /sessions/{pk}/cancel/
#     @action(detail=True, methods=["post"])
#     def cancel(self, request, pk=None):
#         session = self.get_object()
#         MeetService.cancel_session(
#             session, actor=request.user, reason=request.data.get("reason", "")
#         )
#         return Response({"state": session.state})


class TeacherMeetSessionsView(TeacherRequiredMixin, ListView):
    template_name = "apps/tutoring/teacher/meet_sessions.html"
    context_object_name = "sessions"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            GoogleSession.objects.filter(teacher=self.request.user)
            .select_related("student__student_profile")
            .order_by("-created_at")
        )

        state = self.request.GET.get("state", "").strip()
        if state and state in GoogleSession.State.values:
            qs = qs.filter(state=state)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qp = self.request.GET.copy()
        qp.pop("page", None)

        context.update(
            {
                "state_choices": GoogleSession.State.choices,
                "filter_state": self.request.GET.get("state", ""),
                "querystring": qp.urlencode(),
                # counts per state for the tab badges
                "state_counts": (
                    GoogleSession.objects.filter(teacher=self.request.user)
                    .values("state")
                    .annotate(count=Count("id"))
                ),
            }
        )

        return context


class TeacherMeetSessionDetailView(TeacherRequiredMixin, DetailView):
    template_name = "apps/tutoring/teacher/meet_session_detail.html"
    context_object_name = "session"
    pk_url_kwarg = "session_id"

    def get_queryset(self):
        # Teachers can only see their own sessions
        return GoogleSession.objects.filter(teacher=self.request.user).select_related(
            "student__student_profile",
            "teacher__teacher_profile",
        )


class TeacherAcceptSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            GoogleSession,
            pk=session_id,
            teacher=request.user,
            state=GoogleSession.State.PENDING_TEACHER,
        )
        try:
            MeetService.teacher_accept(session)
            messages.success(
                request, _("Session accepted. Student will be notified to pay.")
            )
        except Exception:
            logger.exception("teacher_accept failed for session %s", session_id)
            messages.error(request, _("Unable to accept session. Please try again."))

        return redirect(
            reverse(
                "tutoring:meet:meet-session-detail",
                kwargs={"session_id": session_id},
            )
        )


class TeacherRejectSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            GoogleSession,
            pk=session_id,
            teacher=request.user,
            state=GoogleSession.State.PENDING_TEACHER,
        )
        reason = request.POST.get("reason", "").strip()
        try:
            MeetService.teacher_reject(session, reason=reason)
            messages.success(request, _("Session rejected."))
        except Exception:
            logger.exception("teacher_reject failed for session %s", session_id)
            messages.error(request, _("Unable to reject session. Please try again."))

        return redirect(reverse("tutoring:meet:meet-sessions"))


class TeacherStartSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            GoogleSession,
            pk=session_id,
            teacher=request.user,
            state=GoogleSession.State.PAID,
        )
        try:
            MeetService.start_session(session)
            messages.success(request, _("Session started."))
        except Exception:
            logger.exception("start_session failed for session %s", session_id)
            messages.error(request, _("Unable to start session."))

        return redirect(
            reverse(
                "tutoring:meet:meet-session-detail",
                kwargs={"session_id": session_id},
            )
        )


class TeacherCompleteSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            GoogleSession,
            pk=session_id,
            teacher=request.user,
            state=GoogleSession.State.ACTIVE,
        )
        try:
            MeetService.complete_session(session)
            messages.success(request, _("Session marked as completed."))
        except Exception:
            logger.exception("complete_session failed for session %s", session_id)
            messages.error(request, _("Unable to complete session."))

        return redirect(
            reverse(
                "tutoring:meet:meet-session-detail",
                kwargs={"session_id": session_id},
            )
        )


class TeacherCancelSessionView(TeacherRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            GoogleSession,
            pk=session_id,
            teacher=request.user,
            state__in=[
                GoogleSession.State.PENDING_TEACHER,
                GoogleSession.State.PENDING_PAYMENT,
            ],
        )
        reason = request.POST.get("reason", "").strip()
        try:
            MeetService.cancel_session(session, actor=request.user, reason=reason)
            messages.success(request, _("Session cancelled."))
        except Exception:
            logger.exception("cancel_session failed for session %s", session_id)
            messages.error(request, _("Unable to cancel session."))

        return redirect(reverse("tutoring:teacher:meet-sessions"))


class StudentMeetSessionsView(StudentRequiredMixin, ListView):
    template_name = "apps/tutoring/student/meet_sessions.html"
    context_object_name = "sessions"
    paginate_by = 15

    def get_queryset(self):
        qs = (
            GoogleSession.objects.filter(student=self.request.user)
            .select_related("teacher__teacher_profile")
            .order_by("-created_at")
        )

        state = self.request.GET.get("state", "").strip()
        if state and state in GoogleSession.State.values:
            qs = qs.filter(state=state)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        qp = self.request.GET.copy()
        qp.pop("page", None)

        context.update(
            {
                "state_choices": GoogleSession.State.choices,
                "filter_state": self.request.GET.get("state", ""),
                "querystring": qp.urlencode(),
                "state_counts": (
                    GoogleSession.objects.filter(student=self.request.user)
                    .values("state")
                    .annotate(count=Count("id"))
                ),
            }
        )

        return context


class StudentMeetSessionDetailView(StudentRequiredMixin, DetailView):
    template_name = "apps/tutoring/student/meet_session_detail.html"
    context_object_name = "session"
    pk_url_kwarg = "session_id"

    def get_queryset(self):
        return GoogleSession.objects.filter(student=self.request.user).select_related(
            "teacher__teacher_profile",
            "student__student_profile",
        )


class StudentCancelMeetSessionView(StudentRequiredMixin, View):

    def post(self, request, session_id):
        session = get_object_or_404(
            GoogleSession,
            pk=session_id,
            student=request.user,
            state__in=[
                GoogleSession.State.PENDING_TEACHER,
                GoogleSession.State.PENDING_PAYMENT,
            ],
        )
        reason = request.POST.get("reason", "").strip()
        try:
            MeetService.cancel_session(session, actor=request.user, reason=reason)
            messages.success(request, _("Session cancelled successfully."))
        except Exception:
            logger.exception("student cancel_session failed for session %s", session_id)
            messages.error(request, _("Unable to cancel session. Please try again."))

        return redirect(reverse("tutoring:student:meet-sessions"))


class StudentMeetSessionPayView(StudentRequiredMixin, View):

    def get(self, request, session_id):
        session = get_object_or_404(
            GoogleSession,
            pk=session_id,
            student=request.user,
            state=GoogleSession.State.PENDING_PAYMENT,
        )

        try:
            checkout = StripeService.create_meet_checkout_session(
                student=request.user,
                session=session,
            )

            if not checkout:
                raise Exception("Stripe checkout creation failed.")

            return redirect(checkout.url)

        except Exception as ex:
            logger.exception("meet session pay failed: %s", str(ex))
            messages.error(request, _("Unable to initiate payment. Please try again."))
            return redirect(
                reverse(
                    "tutoring:meet:student-meet-session-detail",
                    kwargs={"session_id": session_id},
                )
            )

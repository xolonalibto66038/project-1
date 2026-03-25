import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.accounts.choices import UserRole
from apps.accounts.models import CustomUser
from apps.authentication.decorators import student_required
from apps.billing.choices import OfferTier
from apps.billing.decorators import subscription_required
from apps.billing.exceptions import SubscriptionRequired
from apps.billing.services import StripeService

from ..decorators import teacher_level_required
from ..models import TutoringSession
from ..services import SessionService
from ..services.meet import MeetService

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

logger = logging.getLogger(__name__)


@login_required
@student_required
@subscription_required
def available_teachers(request, subject_pk=None):

    teachers = (
        CustomUser.objects.filter(
            role=UserRole.TEACHER,
            is_active=True,
            teacher_profile__is_verified_teacher=True,
        )
        .select_related("teacher_profile")
        .prefetch_related("teacher_profile__subject")
        .only(
            "id",
            "first_name",
            "last_name",
            "avatar",
            "teacher_profile__bio",
        )
        .order_by("last_name")
    )

    if subject_pk:
        teachers = teachers.filter(teacher_profile__subject__id=subject_pk)

    free_teachers = teachers.filter(teacher_profile__hour_price=0)
    paid_teachers = teachers.filter(teacher_profile__hour_price__gt=0)

    # Build full breadcrumb path if subject is provided
    crumbs = [
        {"label": "Home", "url": reverse("pages:landing"), "icon": "fas fa-home"},
    ]

    if subject_pk:
        from apps.curriculum.models import GradeSubject

        gs = (
            GradeSubject.objects.select_related("grade__level", "subject", "specialty")
            .filter(subject__id=subject_pk)
            .first()
        )

        if gs:
            grade = gs.grade
            level = grade.level
            specialty = gs.specialty

            grade_url = reverse(
                "curriculum:grade:grade-detail", kwargs={"pk": grade.pk}
            )
            if specialty:
                grade_url += f"?specialty={specialty.pk}"

            crumbs += [
                {"label": "Levels", "url": reverse("curriculum:level:level-list")},
                {
                    "label": level.name,
                    "url": reverse(
                        "curriculum:level:level-detail", kwargs={"pk": level.pk}
                    ),
                },
                {
                    "label": gs.subject.short_name,
                    "url": reverse(
                        "curriculum:grade-subject:grade-subject-detail",
                        kwargs={"pk": gs.pk},
                    ),
                },
            ]

    crumbs.append({"label": "Online Teachers", "url": None})

    context = {
        "free_teachers": free_teachers,
        "paid_teachers": paid_teachers,
        "subject_pk": subject_pk,
        "crumbs": crumbs,
    }

    return render(request, "apps/tutoring/student/available_teachers.html", context)


@login_required
@student_required
# @premium_required
@subscription_required(tier=OfferTier.PREMIUM)  # same as above, explicit
@teacher_level_required
@require_POST
def select_teacher(request, teacher_id):
    # teacher is re-fetched here — decorator already validated it exists
    # and the level matches. A second get_object_or_404 is acceptable
    # because select_related avoids extra queries on the hot path.
    teacher = get_object_or_404(
        CustomUser.objects.select_related(
            "teacher_profile__subject__level",
        ),
        id=teacher_id,
        role=UserRole.TEACHER,
        is_active=True,
        teacher_profile__is_verified_teacher=True,
    )

    try:
        # FREE teacher → create session directly, no Stripe
        if teacher.teacher_profile.hour_price == 0:
            SessionService.create_free_session(
                student=request.user,
                teacher=teacher,
            )
            return redirect("tutoring:student:student-sessions")

        # PAID teacher → create Stripe checkout only, no DB session yet
        checkout = StripeService.create_checkout_session(
            student=request.user,
            teacher=teacher,
        )

        if not checkout:
            raise Exception("Stripe checkout session creation failed")

        return redirect(checkout.url)

    except SubscriptionRequired:
        raise
    except Exception as ex:
        logger.exception(
            f"Exception : {str(ex)}, select_teacher: session creation failed for "
            "student pk=%s teacher pk=%s.",
            request.user.pk,
            teacher.pk,
        )
        messages.error(
            request,
            _("Unable to create session. Please try again."),
        )
        return redirect(
            "tutoring:student:available-teachers",
            subject_pk=teacher.teacher_profile.subject.pk,
        )


@login_required
@student_required
@teacher_level_required
@require_POST
def meet_teacher(request, teacher_id):
    teacher = get_object_or_404(
        CustomUser.objects.select_related("teacher_profile"),
        id=teacher_id,
        role=UserRole.TEACHER,
        is_active=True,
        teacher_profile__is_verified_teacher=True,
    )

    proposed_start_raw = request.POST.get("proposed_start")
    proposed_end_raw = request.POST.get("proposed_end")

    if not proposed_start_raw or not proposed_end_raw:
        messages.error(request, _("Please provide a proposed start and end time."))
        return redirect("tutoring:student:available-teachers")

    try:
        proposed_start = timezone.datetime.fromisoformat(proposed_start_raw)
        proposed_end = timezone.datetime.fromisoformat(proposed_end_raw)
    except ValueError:
        messages.error(request, _("Invalid date format."))
        return redirect("tutoring:student:available-teachers")

    if proposed_start >= proposed_end:
        messages.error(request, _("End time must be after start time."))
        return redirect("tutoring:student:available-teachers")

    try:
        MeetService.request_session(
            student=request.user,
            teacher=teacher,
            proposed_start=proposed_start,
            proposed_end=proposed_end,
            notes=request.POST.get("student_notes", ""),
        )
        messages.success(
            request, _("Session request sent. Waiting for teacher approval.")
        )
        return redirect("tutoring:student:student-sessions")

    except ValueError as e:
        messages.error(request, str(e))
        return redirect("tutoring:student:available-teachers")
    except Exception as ex:
        logger.exception("meet_teacher failed: %s", str(ex))
        messages.error(request, _("Unable to create session. Please try again."))
        return redirect("tutoring:student:available-teachers")


@login_required
@student_required
@subscription_required
def student_sessions(request):

    sessions = (
        TutoringSession.objects.filter(
            student=request.user,
        )
        .select_related("teacher")
        .order_by("-created_at")
    )

    return render(
        request,
        "apps/tutoring/student/student_sessions.html",
        {"sessions": sessions},
    )


@login_required
@student_required
@subscription_required
def session_detail(request, session_id):
    """
    Display tutoring session details for the student.

    Security:
    - Ensures the logged-in user owns the session.
    - Prevents access to other users' sessions.
    """

    session = get_object_or_404(
        TutoringSession.objects.select_related(
            "teacher",
            "teacher__teacher_profile",
            "student",
        ),
        id=session_id,
        student_id=request.user.id,
    )

    context = {
        "session": session,
    }

    return render(
        request,
        "apps/tutoring/student/session_detail.html",
        context,
    )

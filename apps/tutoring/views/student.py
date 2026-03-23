import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.choices import UserRole
from apps.accounts.models import CustomUser
from apps.authentication.decorators import student_required
from apps.billing.decorators import subscription_required
from apps.billing.services import StripeService

from ..models import TutoringSession
from ..services import SessionService

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


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
                # {
                #     "label": f"{grade.name}{' | ' + specialty.short_name if specialty else ''}",
                #     "url": grade_url,
                # },
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
@subscription_required
@require_POST
def select_teacher(request, teacher_id):
    print()
    teacher = get_object_or_404(
        CustomUser,
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

    except Exception as ex:
        messages.error(
            request, f"Unable to create session. Please try again. {str(ex)}"
        )
        return redirect(
            "tutoring:student:available-teachers",
            subject_pk=teacher.teacher_profile.subject.pk,
        )


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

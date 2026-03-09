import stripe

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from apps.authentication.decorators import student_required
from apps.accounts.choices import UserRole
from apps.accounts.models import CustomUser
from apps.billing.decorators import subscription_required
from apps.billing.services import StripeService
from django.conf import settings

from ..services import SessionService
from ..models import TutoringSession

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


@login_required
@student_required
@subscription_required
def available_teachers(request, subject_pk=None):
    """
    Display list of available teachers for tutoring.

    Filters:
    - role = TEACHER
    - active users only
    - verified teachers only (recommended)
    - optional subject filter
    """

    # for better performance, prefetch related subjects
    teachers = (
        CustomUser.objects.filter(
            role=UserRole.TEACHER,
            is_active=True,
            teacher_profile__is_verified_teacher =True,
        )
        .select_related("teacher_profile")
        .prefetch_related("teacher_profile__subject")
        .only(
            "id",
            "first_name",
            "last_name",
            "avatar",
            # "teacher_profile__average_rating",
            # "teacher_profile__years_of_experience",
            "teacher_profile__bio",
        )
        .order_by(
            "last_name"
            # "-teacher_profile__average_rating",
            # "-teacher_profile__years_of_experience",
        )
    )

    # Optional: filter by subject
    if subject_pk:
        teachers = teachers.filter(teacher_profile__subject__id=subject_pk)

    context = {
        "teachers": teachers,
        "subject_pk": subject_pk,
    }

    return render(request, "apps/tutoring/student/available_teachers.html", context)


@login_required
@student_required
@subscription_required
@require_POST
@transaction.atomic
def select_teacher(request, teacher_id):

    teacher = get_object_or_404(
        CustomUser,
        id=teacher_id,
        role=UserRole.TEACHER,
        is_active=True,
        teacher_profile__is_verified_teacher=True,
    )

    try:

        session, created = SessionService.create_session(
            student=request.user,
            teacher=teacher,
        )

        # Create Stripe checkout session if needed
        if created or not session.stripe_checkout_session_id:

            checkout = StripeService.create_checkout_session(session)

            if not checkout:
                raise Exception("Stripe checkout session creation failed")

            session.stripe_checkout_session_id = checkout.id
            session.save(update_fields=["stripe_checkout_session_id"])

        else:
            # Retrieve existing Stripe checkout session
            checkout = stripe.checkout.Session.retrieve(
                session.stripe_checkout_session_id
            )

        return redirect(checkout.url)

    except Exception as ex:
        print(f"Failed to create tutoring session : {str(ex)}")

        messages.error(request, "Unable to create session. Please try again.")

        return redirect(
            "tutoring:student:available-teachers",
            subject_pk=teacher.teacher_profile.subject.pk
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
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.tutoring.models import ZoomSession


class SessionService:

    @staticmethod
    @transaction.atomic
    def create_free_session(student, teacher):
        teacher = (
            teacher.__class__.objects.select_for_update()
            .select_related("teacher_profile")
            .get(id=teacher.id)
        )

        if teacher.id == student.id:
            raise ValueError("Cannot book yourself")

        # Block duplicate confirmed free session
        existing = ZoomSession.objects.filter(
            student=student,
            teacher=teacher,
            status=ZoomSession.Status.CONFIRMED,
            started_at__isnull=True,
        ).first()

        if existing:
            raise ValueError("You already have a confirmed session with this teacher.")

        profile = teacher.teacher_profile
        platform_fee_percent = getattr(settings, "PLATFORM_FEE_PERCENT", 10)
        platform_fee = Decimal("0")
        teacher_amount = Decimal("0")

        return ZoomSession.objects.create(
            student=student,
            teacher=teacher,
            price=Decimal("0"),
            platform_fee=platform_fee,
            teacher_amount=teacher_amount,
            status=ZoomSession.Status.PAYMENT_AUTHORIZED,
        )

    @staticmethod
    @transaction.atomic
    def create_paid_session(
        student, teacher, stripe_checkout_session_id, stripe_payment_intent_id
    ):
        teacher = (
            teacher.__class__.objects.select_for_update()
            .select_related("teacher_profile")
            .get(id=teacher.id)
        )

        if teacher.id == student.id:
            raise ValueError("Cannot book yourself")

        profile = teacher.teacher_profile
        price = profile.hour_price
        platform_fee_percent = getattr(settings, "PLATFORM_FEE_PERCENT", 10)
        platform_fee = (price * Decimal(platform_fee_percent)) / Decimal("100")
        teacher_amount = price - platform_fee

        return ZoomSession.objects.create(
            student=student,
            teacher=teacher,
            price=price,
            platform_fee=platform_fee,
            teacher_amount=teacher_amount,
            status=ZoomSession.Status.PAYMENT_AUTHORIZED,
            stripe_checkout_session_id=stripe_checkout_session_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            payment_authorized_at=timezone.now(),
        )


# class SessionService:

#     @staticmethod
#     @transaction.atomic
#     def create_session(student, teacher):

#         # Lock teacher row to prevent race conditions
#         teacher = (
#             teacher.__class__.objects.select_for_update()
#             .select_related("teacher_profile")
#             .get(id=teacher.id)
#         )

#         if teacher.id == student.id:
#             raise ValueError("Cannot book yourself")

#         # hourly_rate = teacher.teacher_profile.hourly_rate
#         profile = getattr(teacher, "teacher_profile", None)
#         hourly_rate = getattr(profile, "hour_price", 100) if profile else 100
#         is_free = hourly_rate == 0

#         # ✅ 🚫 BLOCK: existing confirmed free session not started yet
#         if is_free:
#             existing_free = (
#                 ZoomSession.objects.select_for_update()
#                 .filter(
#                     student=student,
#                     teacher=teacher,
#                     price=0,
#                     status=ZoomSession.Status.CONFIRMED,
#                     started_at__isnull=True,  # not started yet
#                 )
#                 .first()
#             )

#             if existing_free:
#                 raise ValueError(
#                     "You already have a confirmed session with this teacher."
#                 )

#         status = ZoomSession.Status.PENDING_PAYMENT

#         # if is_free:
#         #     raise ValueError("Invalid teacher rate")

#         # ✅ Prevent duplicate pending sessions (fix your bug)
#         pending_status = (
#             ZoomSession.Status.PAYMENT_AUTHORIZED
#             if is_free
#             else ZoomSession.Status.PENDING_PAYMENT
#         )

#         # Prevent duplicate pending sessions
#         existing = (
#             ZoomSession.objects.select_for_update()
#             .filter(
#                 student=student,
#                 teacher=teacher,
#                 status=pending_status,
#             )
#             .first()
#         )

#         if existing:
#             return existing, False

#         price = hourly_rate

#         platform_fee_percent = getattr(settings, "PLATFORM_FEE_PERCENT", 10)

#         platform_fee = (price * Decimal(platform_fee_percent)) / Decimal("100")

#         teacher_amount = price - platform_fee

#         status = (
#             ZoomSession.Status.PAYMENT_AUTHORIZED
#             if is_free
#             else ZoomSession.Status.PENDING_PAYMENT
#         )

#         session = ZoomSession.objects.create(
#             student=student,
#             teacher=teacher,
#             price=price,
#             platform_fee=platform_fee,
#             teacher_amount=teacher_amount,
#             status=status,
#         )

#         return session, True

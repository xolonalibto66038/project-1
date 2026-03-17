from celery import shared_task


@shared_task(name="apps.tutoring.tasks.cleanup_unpaid_sessions")
def cleanup_unpaid_sessions():
    from datetime import timedelta

    from django.utils import timezone

    from apps.tutoring.models import TutoringSession

    now = timezone.now()

    deleted_count, _ = TutoringSession.objects.filter(
        status__in=[
            TutoringSession.Status.PENDING_PAYMENT,
            TutoringSession.Status.PAYMENT_FAILED,
        ],
        scheduled_at__lt=now - timedelta(hours=1),
    ).delete()

    return f"Deleted {deleted_count} unpaid/failed sessions"


@shared_task(name="apps.tutoring.tasks.cancel_noshow_sessions")
def cancel_noshow_sessions():
    from datetime import timedelta

    from django.utils import timezone

    from apps.tutoring.models import TutoringSession

    now = timezone.now()
    cutoff = now - timedelta(hours=2)  # 2h grace period after scheduled_at

    noshow_sessions = TutoringSession.objects.filter(
        status=TutoringSession.Status.CONFIRMED,
        scheduled_at__lt=cutoff,
        started_at__isnull=True,
    )

    updated_count = 0
    for session in noshow_sessions:
        session.status = TutoringSession.Status.CANCELED
        session.save(update_fields=["status"])
        # TODO: trigger refund task here → refund_session.delay(session.id)
        updated_count += 1

    return f"Canceled {updated_count} no-show sessions"

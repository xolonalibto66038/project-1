import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .helpers import trigger_teacher_payout
from .models import TutoringSession


@csrf_exempt
@login_required
def zoom_webhook(request):

    # Verify Zoom signature (CRITICAL)
    if not verify_zoom_signature(request):

        # logger.warning("Invalid Zoom signature")

        return HttpResponse(status=400)

    payload = json.loads(request.body.decode())

    event = payload.get("event")

    # -----------------------------------------------------
    # ZOOM ENDPOINT VALIDATION (REQUIRED)
    # -----------------------------------------------------

    if event == "endpoint.url_validation":

        plain_token = payload["payload"]["plainToken"]

        encrypted_token = hmac.new(
            settings.ZOOM_WEBHOOK_SECRET.encode(),
            plain_token.encode(),
            hashlib.sha256,
        ).hexdigest()

        return JsonResponse(
            {
                "plainToken": plain_token,
                "encryptedToken": encrypted_token,
            }
        )

    meeting_id = str(payload["payload"]["object"]["id"])

    try:

        session = TutoringSession.objects.get(zoom_meeting_id=meeting_id)

    except TutoringSession.DoesNotExist:

        return HttpResponse(status=200)

    # -----------------------------------------------------
    # MEETING STARTED
    # -----------------------------------------------------

    if event == "meeting.started":

        session.status = TutoringSession.Status.IN_PROGRESS

        session.started_at = timezone.now()

        session.save(
            update_fields=[
                "status",
                "started_at",
                "updated_at",
            ]
        )

    # -----------------------------------------------------
    # MEETING ENDED
    # -----------------------------------------------------

    elif event == "meeting.ended":

        session.status = TutoringSession.Status.COMPLETED

        session.completed_at = timezone.now()

        session.save(
            update_fields=[
                "status",
                "completed_at",
                "updated_at",
            ]
        )

        # Trigger payout async (Celery recommended)
        trigger_teacher_payout(session)

    return HttpResponse(status=200)


def verify_zoom_signature(request):

    signature = request.headers.get("x-zm-signature")
    timestamp = request.headers.get("x-zm-request-timestamp")

    message = f"v0:{timestamp}:{request.body.decode()}"

    hash = hmac.new(
        settings.ZOOM_WEBHOOK_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()

    expected = f"v0={hash}"

    return hmac.compare_digest(signature, expected)

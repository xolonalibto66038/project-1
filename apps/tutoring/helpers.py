import json
import logging
import secrets
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import stripe
from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def trigger_teacher_payout(session):

    if session.teacher_paid:
        return

    transfer = stripe.Transfer.create(
        amount=int(session.teacher_amount * 100),
        currency="usd",
        destination=session.teacher.stripe_account_id,
    )

    session.teacher_paid = True

    session.teacher_paid_at = timezone.now()

    session.stripe_transfer_id = transfer.id

    session.save()


def convert_to_browser_join_url(zoom_join_url: str) -> str:
    """
    Convert a standard Zoom join URL to a direct browser join URL.
    Example:
    https://us05web.zoom.us/j/123456789?pwd=abc
    ->
    https://app.zoom.us/wc/123456789/join?pwd=abc
    """
    parsed = urlparse(zoom_join_url)

    # Extract meeting ID from path: /j/123456789
    path_parts = parsed.path.strip("/").split("/")
    meeting_id = path_parts[-1]

    query_params = parse_qs(parsed.query)
    pwd = query_params.get("pwd", [""])[0]

    browser_url = f"https://app.zoom.us/wc/{meeting_id}/join"

    if pwd:
        browser_url += f"?pwd={pwd}"

    return browser_url


def redirect_back(request):
    """Fallback redirect if no referer."""
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("pages:landing")


def _get_calendar_service():
    creds = Credentials.from_authorized_user_file(
        settings.GOOGLE_TOKEN_FILE,
        settings.GOOGLE_CALENDAR_SCOPES,
    )

    # Auto-refresh if expired
    if creds.expired and creds.refresh_token:
        logger.info("Refreshing Google OAuth token...")
        creds.refresh(Request())
        # Save refreshed token back to file
        with open(settings.GOOGLE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _persist_refreshed_token(creds: Credentials):
    """
    Persist the refreshed access token so the next call
    doesn't have to hit Google's token endpoint again.
    Store it in DB or cache — not in .env (that's read-only at runtime).
    """
    from django.core.cache import cache

    cache.set(
        "google_oauth_token",
        creds.token,
        timeout=3500,  # tokens last ~1 hour
    )


def create_meet_event(session) -> dict:
    """
    Creates a Google Calendar event with an embedded Meet link.
    Returns a dict with event_id, meet_link, html_link.
    Raises GoogleMeetError on failure.
    """
    service = _get_calendar_service()

    start_dt: datetime = session.confirmed_start
    end_dt: datetime = session.confirmed_end

    # Ensure timezone-aware ISO 8601
    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(start_dt)
    if timezone.is_naive(end_dt):
        end_dt = timezone.make_aware(end_dt)

    tz_name = settings.GOOGLE_MEET_DEFAULT_TIMEZONE

    event_body = {
        "summary": f"Tutoring: {session.teacher.get_full_name()} → {session.student.get_full_name()}",
        "description": (
            f"Session #{session.pk}\n"
            f"Duration: {session.duration_minutes} minutes\n"
            f"Notes: {session.student_notes or '—'}"
        ),
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": tz_name,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": tz_name,
        },
        # Embed both parties as attendees (informational — service account owns the event)
        "attendees": [
            {
                "email": session.student.email,
                "displayName": session.student.get_full_name(),
            },
            {
                "email": session.teacher.email,
                "displayName": session.teacher.get_full_name(),
            },
        ],
        # This is the magic: request a Meet conference room
        "conferenceData": {
            "createRequest": {
                "requestId": f"session-{session.pk}-{secrets.token_hex(4)}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 15},
            ],
        },
        # Participant controls
        "guestsCanSeeOtherGuests": False,
        "guestsCanInviteOthers": False,
    }

    try:
        created = (
            service.events()
            .insert(
                calendarId="primary",
                body=event_body,
                conferenceDataVersion=1,  # required to generate Meet link
                sendUpdates="all",  # sends calendar invites to attendees
            )
            .execute()
        )
    except HttpError as e:
        logger.exception("Google Calendar API error for session %s: %s", session.pk, e)
        raise GoogleMeetError(f"Google Calendar API error: {e}") from e

    meet_link = (
        created.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri", "")
    )

    return {
        "event_id": created["id"],
        "meet_link": meet_link,
        "html_link": created.get("htmlLink", ""),  # "open in Google Calendar"
    }


def cancel_meet_event(google_event_id: str) -> None:
    """Deletes the calendar event and invalidates the Meet link."""
    service = _get_calendar_service()
    try:
        service.events().delete(
            calendarId="primary",
            eventId=google_event_id,
            sendUpdates="all",
        ).execute()
    except HttpError as e:
        logger.warning("Could not delete calendar event %s: %s", google_event_id, e)


def update_meet_event(session) -> None:
    """Patches start/end time on an existing event (e.g. teacher reschedules)."""
    if not session.google_event_id:
        return
    service = _get_calendar_service()
    patch_body = {
        "start": {
            "dateTime": session.confirmed_start.isoformat(),
            "timeZone": settings.GOOGLE_MEET_DEFAULT_TIMEZONE,
        },
        "end": {
            "dateTime": session.confirmed_end.isoformat(),
            "timeZone": settings.GOOGLE_MEET_DEFAULT_TIMEZONE,
        },
    }
    try:
        service.events().patch(
            calendarId="primary",
            eventId=session.google_event_id,
            body=patch_body,
            sendUpdates="all",
        ).execute()
    except HttpError as e:
        logger.exception("Could not patch event %s: %s", session.google_event_id, e)


class GoogleMeetError(Exception):
    pass

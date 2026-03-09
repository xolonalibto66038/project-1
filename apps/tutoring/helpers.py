from urllib.parse import parse_qs, urlparse

import stripe
from django.utils import timezone


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

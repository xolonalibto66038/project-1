import base64

import requests
from django.conf import settings


class ZoomService:

    @staticmethod
    def get_access_token():

        url = "https://zoom.us/oauth/token"

        credentials = f"{settings.ZOOM_CLIENT_ID}:{settings.ZOOM_CLIENT_SECRET}"
        credentials_base64 = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {credentials_base64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        params = {
            "grant_type": "account_credentials",
            "account_id": settings.ZOOM_ACCOUNT_ID,
        }

        response = requests.post(url, headers=headers, params=params)

        return response.json()["access_token"]

    @staticmethod
    def create_meeting(session):

        token = ZoomService.get_access_token()

        response = requests.post(
            url=f"{settings.ZOOM_BASE_URL}/users/{settings.ZOOM_HOST_EMAIL}/meetings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "topic": f"Tutoring session {session.id}",
                "type": 2,
                "start_time": session.scheduled_at.isoformat(),
                "duration": session.duration_minutes,
                "settings": {
                    "waiting_room": True,
                    "join_before_host": False,
                    "meeting_authentication": False,
                    "password": "",
                    "passcode": "",
                    "auto_recording": "none",
                    "use_pmi": False,
                    "enforce_login": False,
                },
                # "settings": {"waiting_room": True, "join_before_host": False, "password_required": False, "use_pmi": False,},
            },
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    @staticmethod
    def disable_passcode_requirement():
        """
        Run this once to disable passcode at account level.
        Zoom account settings override per-meeting settings.
        """
        token = ZoomService.get_access_token()

        requests.patch(
            url=f"{settings.ZOOM_BASE_URL}/accounts/me/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "security": {
                    "meeting_password": False,
                    "require_password_for_all": False,
                }
            },
            timeout=10,
        )

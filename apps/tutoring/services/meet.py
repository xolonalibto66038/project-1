# # apps/tutoring/services/meet.py

# from django.conf import settings
# from google.oauth2 import service_account
# from googleapiclient.discovery import build


# class MeetService:

#     SCOPES = ["https://www.googleapis.com/auth/calendar"]

#     @staticmethod
#     def _get_service():
#         credentials = service_account.Credentials.from_service_account_file(
#             settings.GOOGLE_SERVICE_ACCOUNT_FILE,
#             scopes=MeetService.SCOPES,
#             subject=settings.GOOGLE_CALENDAR_HOST_EMAIL,  # impersonate this user
#         )
#         return build("calendar", "v3", credentials=credentials)

#     @staticmethod
#     def create_meeting(session):
#         """
#         Creates a Google Calendar event with a Meet link.
#         Returns dict with join_url and event_id.
#         """
#         service = MeetService._get_service()

#         start = session.scheduled_at
#         end = start + __import__("datetime").timedelta(minutes=session.duration_minutes)

#         event = (
#             service.events()
#             .insert(
#                 calendarId="primary",
#                 conferenceDataVersion=1,  # required to generate Meet link
#                 sendUpdates="all",  # emails invites to attendees
#                 body={
#                     "summary": f"Tutoring session — {session.teacher.get_full_name()}",
#                     "description": (
#                         f"Student: {session.student.get_full_name()}\n"
#                         f"Teacher: {session.teacher.get_full_name()}\n"
#                         f"Session ID: {session.id}"
#                     ),
#                     "start": {
#                         "dateTime": start.isoformat(),
#                         "timeZone": "UTC",
#                     },
#                     "end": {
#                         "dateTime": end.isoformat(),
#                         "timeZone": "UTC",
#                     },
#                     "attendees": [
#                         {"email": session.student.email},
#                         {"email": session.teacher.email},
#                     ],
#                     "conferenceData": {
#                         "createRequest": {
#                             "requestId": str(session.id),
#                             "conferenceSolutionKey": {"type": "hangoutsMeet"},
#                         }
#                     },
#                 },
#             )
#             .execute()
#         )

#         join_url = (
#             event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri", "")
#         )

#         return {
#             "event_id": event["id"],
#             "join_url": join_url,
#             "start_url": join_url,  # Meet has no separate host URL
#         }

#     @staticmethod
#     def delete_meeting(event_id: str):
#         service = MeetService._get_service()
#         service.events().delete(
#             calendarId="primary",
#             eventId=event_id,
#         ).execute()

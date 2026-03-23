# class BookmarkToggleService:
#     """
#     Single responsibility: toggle a bookmark and optionally update its note.

#     Separates the get_or_create + note-update logic from the view so both
#     are independently testable.
#     """

#     def toggle(
#         self,
#         student: object,
#         content_type: object,
#         object_id: object,
#         note: str = "",
#     ) -> tuple[object, bool]:
#         """
#         Returns (bookmark, is_now_active).

#         - New bookmark   → created active, note saved if provided
#         - Existing + active   → deactivated (note preserved)
#         - Existing + inactive → reactivated, note updated if provided
#         """
#         from ..models import Bookmark

#         bookmark, created = Bookmark.objects.get_or_create(
#             student=student,
#             content_type=content_type,
#             object_id=object_id,
#             defaults={"active": True, "note": note},
#         )

#         if not created:
#             if bookmark.active:
#                 # toggling off — preserve existing note
#                 bookmark.active = False
#                 bookmark.save(update_fields=["active", "updated_at"])
#             else:
#                 # reactivating — update note if a new one was supplied
#                 bookmark.active = True
#                 if note:
#                     bookmark.note = note
#                 bookmark.save(update_fields=["active", "note", "updated_at"])

#         return bookmark, bookmark.active

from dataclasses import dataclass

from django.http import HttpRequest

from ..models import Bookmark


class BookmarkToggleService:

    def toggle(self, student, content_type, object_id, note=""):
        """Flip active state."""
        bookmark, created = Bookmark.objects.get_or_create(
            student=student,
            content_type=content_type,
            object_id=object_id,
            defaults={"note": note, "active": True},
        )
        if not created:
            bookmark.active = not bookmark.active
            if bookmark.active:
                bookmark.note = note
            bookmark.save(update_fields=["active", "note"])
        return bookmark, bookmark.active

    def save(self, student, content_type, object_id, note=""):
        """Create or reactivate, always updating the note."""
        bookmark, _ = Bookmark.objects.update_or_create(
            student=student,
            content_type=content_type,
            object_id=object_id,
            defaults={"note": note, "active": True},
        )
        return bookmark, True

    def remove(self, student, content_type, object_id):
        """Soft-delete: mark inactive."""
        bookmark = Bookmark.objects.filter(
            student=student,
            content_type=content_type,
            object_id=object_id,
        ).first()
        if bookmark:
            bookmark.active = False
            bookmark.save(update_fields=["active"])
        return bookmark, False


@dataclass(frozen=True)
class BookmarkFilters:
    q: str = ""  # searches note
    content_type: str = ""  # e.g. "videoresource" | "resource"
    querystring: str = ""  # rebuilt QS for pagination / links


class BookmarkFilterExtractor:
    """
    Extracts and normalises bookmark list filters from the request.
    Allowed content_type values are validated against Bookmark.ALLOWED_MODELS
    to prevent arbitrary filtering.
    """

    def extract(self, request: HttpRequest, allowed_models: tuple) -> BookmarkFilters:
        q = request.GET.get("q", "").strip()
        raw_ct = request.GET.get("type", "").strip().lower()

        # Whitelist — reject any value not in ALLOWED_MODELS
        content_type = raw_ct if raw_ct in allowed_models else ""

        parts = []
        if q:
            parts.append(f"q={q}")
        if content_type:
            parts.append(f"type={content_type}")

        return BookmarkFilters(
            q=q,
            content_type=content_type,
            querystring="&".join(parts),
        )

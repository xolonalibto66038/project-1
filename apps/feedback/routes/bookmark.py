from django.urls import path

from ..views.bookmark import (
    BookmarkResourceView,
    BookmarkVideoView,
    StudentBookmarkListView,
)

app_name = "bookmark"

# We define urlpatterns here so it can be easily imported
urlpatterns = [
    # urls.py
    path(
        "<uuid:pk>/resource/",
        BookmarkResourceView.as_view(),
        name="bookmark-resource",
    ),
    path(
        "<uuid:pk>/bookmark/",
        BookmarkVideoView.as_view(),
        name="video-bookmark",
    ),
    path(
        "my-bookmarks/",
        StudentBookmarkListView.as_view(),
        name="student-bookmarks",
    ),
]

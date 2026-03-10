from django.urls import path

from ..views.bookmark import BookmarkResourceView, StudentBookmarkListView

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
        "my-bookmarks/",
        StudentBookmarkListView.as_view(),
        name="student-bookmarks",
    ),
]

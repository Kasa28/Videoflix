from django.urls import path
from .views import VideoPartView, VideoPlaylistView, VideoSegmentView

urlpatterns = [
    path("video/", VideoPartView.as_view(), name="video-part"),
    path(
        "video/<int:movie_id>/<str:resolution>/index.m3u8",
        VideoPlaylistView.as_view(),
        name="video-playlist",
    ),
    path(
        "video/<int:movie_id>/<str:resolution>/<str:segment>/",
        VideoSegmentView.as_view(),
        name="video-segment",
    ),
]

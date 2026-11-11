"""Protected API views for listing and streaming videos."""
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from video_app.models import Video
from video_app.utils import hls_file_path, is_allowed_resolution, is_safe_segment
from .serializers import VideoSerializer

class VideoPartView(ListAPIView):
    """Return video metadata ordered from newest to oldest."""

    permission_classes = [IsAuthenticated]
    queryset = Video.objects.order_by("-created_at")
    serializer_class = VideoSerializer


class VideoPlaylistView(APIView):
    """Serve an HLS playlist for one video and resolution."""

    permission_classes = [IsAuthenticated]
    def get(self, request, movie_id, resolution):
        """Open and return the requested M3U8 playlist."""
        video = get_object_or_404(Video, id=movie_id)
        file = open_video(video, resolution, "index.m3u8")
        return FileResponse(file, content_type="application/vnd.apple.mpegurl")


class VideoSegmentView(APIView):
    """Serve a validated HLS transport-stream segment."""

    permission_classes = [IsAuthenticated]
    def get(self, request, movie_id, resolution, segment):
        """Validate the segment name and return its binary content."""
        video = get_object_or_404(Video, id=movie_id)
        if not is_safe_segment(segment):
            raise Http404("Segment nicht verfügbar.")
        file = open_video(video, resolution, segment)
        return FileResponse(file, content_type="video/mp2t")


def open_video(video, resolution, filename):
    """Open a generated HLS file or raise an HTTP 404 response."""
    if not video.video_file or not is_allowed_resolution(resolution):
        raise Http404("Videoauflösung nicht verfügbar.")
    path = hls_file_path(video.video_file.path, resolution, filename)
    try:
        return path.open("rb")
    except FileNotFoundError:
        raise Http404("Videodatei nicht verfügbar.")

"""Integration tests for video metadata and HLS streaming endpoints."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from video_app.models import Video

User = get_user_model()

class VideoTests(APITestCase):
    """Verify authentication, metadata, playlists, and segments."""

    def setUp(self):
        """Create isolated media storage and one authenticated test user."""
        self.folder = TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.folder.name)
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)
        self.addCleanup(self.folder.cleanup)
        self.user = User.objects.create_user("viewer", password="StrongPass123!")

    def login(self):
        """Attach a valid JWT access cookie to the test client."""
        token = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(token.access_token)

    @patch("video_app.signals._enqueue_video")
    def add_video(self, mock_task, title="Movie"):
        """Create a video while preventing a real background job."""
        file = SimpleUploadedFile("movie.mp4", b"video", content_type="video/mp4")
        return Video.objects.create(
            title=title,
            description="Description",
            category="Drama",
            video_file=file
        )

    def add_video_files(self, video):
        """Create minimal playlist and segment fixtures for a video."""
        folder = Path(video.video_file.path).parent / "movie" / "480p"
        folder.mkdir(parents=True)
        (folder / "index.m3u8").write_text("#EXTM3U", encoding="utf-8")
        (folder / "segment_000.ts").write_bytes(b"segment")

    def test_login_required(self):
        """Reject unauthenticated access to the video catalogue."""
        response = self.client.get("/api/video/")
        self.assertEqual(response.status_code, 401)

    def test_video_list(self):
        """Return authenticated video metadata and category values."""
        video = self.add_video()
        self.login()
        response = self.client.get("/api/video/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["id"], video.pk)
        self.assertEqual(response.data[0]["category"], "Drama")

    def test_video_files(self):
        """Stream existing playlists and transport-stream segments."""
        video = self.add_video()
        self.add_video_files(video)
        self.login()
        playlist = self.client.get(f"/api/video/{video.pk}/480p/index.m3u8")
        segment = self.client.get(f"/api/video/{video.pk}/480p/segment_000.ts/")
        self.assertEqual(playlist.status_code, 200)
        self.assertEqual(segment.status_code, 200)

    def test_wrong_resolution(self):
        """Return HTTP 404 for an unsupported video resolution."""
        video = self.add_video()
        self.login()
        response = self.client.get(f"/api/video/{video.pk}/4k/index.m3u8")
        self.assertEqual(response.status_code, 404)

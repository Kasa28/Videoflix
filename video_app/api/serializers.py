"""Serializers for video metadata returned by the REST API."""
from rest_framework import serializers
from rest_framework.reverse import reverse
from video_app.models import Video

class VideoSerializer(serializers.ModelSerializer):
    """Serialize public video metadata and an absolute thumbnail URL."""
    thumbnail_url = serializers.SerializerMethodField()

    def get_thumbnail_url(self, video):
        """Return the protected thumbnail endpoint after processing."""
        if not video.thumbnail:
            return None
        return reverse(
            "video-thumbnail",
            kwargs={"movie_id": video.pk},
            request=self.context["request"],
        )

    class Meta:
        """Define the video fields exposed to authenticated clients."""

        model = Video
        fields = (
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        )

"""Serializers for video metadata returned by the REST API."""
from rest_framework import serializers
from video_app.models import Video

class VideoSerializer(serializers.ModelSerializer):
    """Serialize public video metadata and an absolute thumbnail URL."""
    thumbnail_url = serializers.SerializerMethodField()

    def get_thumbnail_url(self, video):
        """Return an absolute thumbnail URL when processing is complete."""
        if not video.thumbnail:
            return None
        return self.context["request"].build_absolute_uri(video.thumbnail.url)

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

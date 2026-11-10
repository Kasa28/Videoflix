from rest_framework import serializers
from video_app.models import Video

class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    def get_thumbnail_url(self, video):
        if not video.thumbnail:
            return None
        return self.context["request"].build_absolute_uri(video.thumbnail.url)

    class Meta:
        model = Video
        fields = (
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        )

"""Application configuration for video management and processing."""
from django.apps import AppConfig

class VideoAppConfig(AppConfig):
    """Configure the video app while preserving its historic database label."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'
    label = 'content'
    verbose_name = 'Videos'

    def ready(self):
        """Register video lifecycle signal handlers when Django starts."""
        from . import signals

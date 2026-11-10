from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'
    label = 'content'
    verbose_name = 'Videos'

    def ready(self):
        from . import signals 

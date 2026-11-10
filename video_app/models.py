from django.db import models

class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, default="Other")
    video_file = models.FileField(upload_to="videos/")
    thumbnail = models.FileField(upload_to="thumbnails/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

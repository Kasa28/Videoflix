"""Signals that enqueue processing and remove generated video files."""
import shutil
from pathlib import Path
import django_rq
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from .models import Video
from .tasks import process_video
from .utils import video_output_directory


@receiver(pre_save, sender=Video)
def remember_previous_video_file(sender, instance, **kwargs):
    """Remember the old source path when an existing video is replaced."""
    if not instance.pk:
        instance.previous_video_file = None
        return
    previous = Video.objects.filter(pk=instance.pk).values_list(
        "video_file", flat=True
    ).first()
    current = instance.video_file.name if instance.video_file else None
    instance.previous_video_file = previous if previous != current else None


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    """Queue processing after a video is created or its source is replaced."""
    previous = getattr(instance, "previous_video_file", None)
    if not instance.video_file or not (created or previous):
        return
    transaction.on_commit(
        lambda: _enqueue_video(instance.pk, previous)
    )


def _enqueue_video(video_id, previous=None):
    """Add a video-processing job to the default RQ queue."""
    if previous:
        delete_source_files(Path(settings.MEDIA_ROOT) / previous)
    queue = django_rq.get_queue("default", autocommit=True)
    queue.enqueue(process_video, video_id)


@receiver(post_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    """Delete the source video and generated output after model deletion."""
    if not instance.video_file:
        return
    delete_source_files(Path(instance.video_file.path))


def delete_source_files(source):
    """Delete one source video and its complete generated output tree."""
    shutil.rmtree(video_output_directory(source), ignore_errors=True)
    source.unlink(missing_ok=True)

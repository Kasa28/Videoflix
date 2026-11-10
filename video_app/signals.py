import shutil
from pathlib import Path
import django_rq
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Video
from .tasks import process_video
from .utils import video_output_directory

@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    if not created or not instance.video_file:
        return
    transaction.on_commit(lambda: _enqueue_video(instance.pk))


def _enqueue_video(video_id):
    queue = django_rq.get_queue("default", autocommit=True)
    queue.enqueue(process_video, video_id)


@receiver(post_delete, sender=Video)
def delete_video_files(sender, instance, **kwargs):
    if not instance.video_file:
        return
    source = Path(instance.video_file.path)
    shutil.rmtree(video_output_directory(source), ignore_errors=True)
    source.unlink(missing_ok=True)

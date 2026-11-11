import subprocess
from pathlib import Path
from django.conf import settings
from .models import Video
from .utils import HLS_RESOLUTIONS, video_output_directory

def process_video(video_id):
    video = Video.objects.get(id=video_id)
    source = Path(video.video_file.path)
    folder = video_output_directory(source)
    folder.mkdir(parents=True, exist_ok=True)
    create_thumbnail(source, folder)
    save_thumbnail(video, folder / "thumbnail.jpg")
    for resolution, height in HLS_RESOLUTIONS.items():
        create_hls(source, folder, resolution, height)


def create_thumbnail(source, folder):
    command = [
        "ffmpeg", "-y", "-ss", "00:00:01",
        "-i", str(source), "-frames:v", "1",
        "-q:v", "2", str(folder / "thumbnail.jpg")
    ]
    subprocess.run(command, check=True)


def create_hls(source, folder, resolution, height):
    target = folder / resolution
    target.mkdir(parents=True, exist_ok=True)
    command = hls_command(source, target, height)
    subprocess.run(command, check=True)


def hls_command(source, target, height):
    return [
        "ffmpeg", "-y", "-threads", "2", "-i", str(source),
        "-map", "0:v:0", "-map", "0:a?", "-filter_threads", "1",
        "-vf", f"scale=-2:{height}:flags=fast_bilinear,format=yuv420p",
        "-c:v", "libx264", "-crf", "23",
        "-preset", "veryfast", "-threads", "2", "-c:a", "aac",
        "-hls_time", "10", "-hls_list_size", "0",
        "-hls_segment_filename", str(target / "segment_%03d.ts"),
        "-f", "hls", str(target / "index.m3u8")
    ]


def save_thumbnail(video, thumbnail):
    path = thumbnail.relative_to(settings.MEDIA_ROOT)
    video.thumbnail.name = path.as_posix()
    video.save(update_fields=["thumbnail"])

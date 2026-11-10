import re
from pathlib import Path

HLS_RESOLUTIONS = {"480p": 480, "720p": 720, "1080p": 1080}
SEGMENT_PATTERN = re.compile(r"^segment_\d{3,}\.ts$")

def video_output_directory(source):
    source_path = Path(source)
    return source_path.parent / source_path.stem


def hls_file_path(source, resolution, filename):
    return video_output_directory(source) / resolution / filename


def is_allowed_resolution(resolution):
    return resolution in HLS_RESOLUTIONS


def is_safe_segment(segment):
    return bool(SEGMENT_PATTERN.fullmatch(segment))

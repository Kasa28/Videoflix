"""Shared path and validation helpers for generated HLS files."""
import re
from pathlib import Path

HLS_RESOLUTIONS = {"480p": 480, "720p": 720, "1080p": 1080}
SEGMENT_PATTERN = re.compile(r"^segment_\d{3,}\.ts$")

def video_output_directory(source):
    """Return the generated-output directory beside a source video."""
    source_path = Path(source)
    return source_path.parent / source_path.stem


def hls_file_path(source, resolution, filename):
    """Build the path to one generated playlist or segment."""
    return video_output_directory(source) / resolution / filename


def is_allowed_resolution(resolution):
    """Return whether the requested HLS resolution is supported."""
    return resolution in HLS_RESOLUTIONS


def is_safe_segment(segment):
    """Accept only generated transport-stream segment filenames."""
    return bool(SEGMENT_PATTERN.fullmatch(segment))

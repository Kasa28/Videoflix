import subprocess
from pathlib import Path


def convert_480p(source):
    target = source + "_480p.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-i", source,
        "-s", "hd480",
        "-c:v", "libx264",
        "-crf", "23",
        "-c:a", "aac",
        target,
    ]

    subprocess.run(cmd, check=True)


def convert_to_hls(source):
    source_path = Path(source)
    output_directory = source_path.parent / source_path.stem
    output_directory.mkdir(parents=True, exist_ok=True)

    playlist_path = output_directory / "index.m3u8"
    segment_path = output_directory / "segment_%03d.ts"

    command = [
        "ffmpeg",
        "-y",
        "-i", str(source_path),
        "-c", "copy",
        "-start_number", "0",
        "-hls_time", "10",
        "-hls_list_size", "0",
        "-hls_segment_filename", str(segment_path),
        "-f", "hls",
        str(playlist_path),
    ]

    subprocess.run(command, check=True)

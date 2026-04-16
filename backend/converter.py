"""YouTube → MP3 conversion using yt-dlp + ffmpeg + mutagen."""
from __future__ import annotations

import os
from pathlib import Path

import requests
import yt_dlp
from mutagen.id3 import APIC, ID3, ID3NoHeaderError, TIT2, TPE1
from mutagen.mp3 import MP3

from jobs import JobFile, registry

DOWNLOAD_DIR = Path(os.environ.get("DOWNLOAD_DIR", "./downloads")).resolve()
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _build_ydl_opts(job_id: str, quality: str, playlist: bool) -> dict:
    output_template = str(DOWNLOAD_DIR / job_id / "%(playlist_index)s-%(title)s.%(ext)s")
    if not playlist:
        output_template = str(DOWNLOAD_DIR / job_id / "%(title)s.%(ext)s")

    def progress_hook(data: dict) -> None:
        if data.get("status") == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            done = data.get("downloaded_bytes") or 0
            pct = (done / total * 100) if total else 0
            info = data.get("info_dict") or {}
            registry.update(
                job_id,
                status="running",
                progress=round(pct, 1),
                current_title=info.get("title", ""),
            )

    return {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": not playlist,
        "quiet": True,
        "no_warnings": True,
        "writethumbnail": True,
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            },
        ],
    }


def _embed_tags(mp3_path: Path, info: dict) -> None:
    try:
        tags = ID3(mp3_path)
    except ID3NoHeaderError:
        tags = ID3()

    title = info.get("track") or info.get("title") or mp3_path.stem
    artist = info.get("artist") or info.get("uploader") or "Unknown"
    tags.add(TIT2(encoding=3, text=title))
    tags.add(TPE1(encoding=3, text=artist))

    thumbnail_url = info.get("thumbnail")
    if thumbnail_url:
        try:
            resp = requests.get(thumbnail_url, timeout=10)
            if resp.ok:
                tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=resp.content,
                    )
                )
        except requests.RequestException:
            pass

    tags.save(mp3_path, v2_version=3)


def run_conversion(job_id: str, url: str, quality: str, playlist: bool) -> None:
    """Blocking; meant to be run in a background task/thread."""
    try:
        opts = _build_ydl_opts(job_id, quality, playlist)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        entries = info.get("entries") if "entries" in info else [info]
        job_dir = DOWNLOAD_DIR / job_id

        index = 0
        for entry in entries:
            if entry is None:
                continue
            base = ydl.prepare_filename(entry)
            mp3_path = Path(base).with_suffix(".mp3")
            if not mp3_path.exists():
                # yt-dlp may sanitize differently; find any mp3 matching id
                candidates = list(job_dir.glob(f"*{entry.get('id','')}*.mp3"))
                if candidates:
                    mp3_path = candidates[0]
                else:
                    continue

            _embed_tags(mp3_path, entry)

            registry.add_file(
                job_id,
                JobFile(
                    index=index,
                    title=entry.get("title") or mp3_path.stem,
                    path=str(mp3_path),
                    size_bytes=mp3_path.stat().st_size,
                ),
            )
            index += 1

        registry.update(job_id, status="done", progress=100.0)
    except Exception as exc:  # noqa: BLE001
        registry.update(job_id, status="error", error=str(exc))

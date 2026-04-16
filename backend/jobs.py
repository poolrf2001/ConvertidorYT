"""In-memory job registry.

Stores conversion jobs with status, progress and produced file paths.
A restart wipes the registry; that's acceptable for a prototype.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Literal

JobStatus = Literal["queued", "running", "done", "error"]


@dataclass
class JobFile:
    index: int
    title: str
    path: str
    size_bytes: int


@dataclass
class Job:
    id: str
    url: str
    quality: str
    playlist: bool
    status: JobStatus = "queued"
    progress: float = 0.0
    current_title: str = ""
    error: str | None = None
    files: list[JobFile] = field(default_factory=list)


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, url: str, quality: str, playlist: bool) -> Job:
        job = Job(id=uuid.uuid4().hex, url=url, quality=quality, playlist=playlist)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in fields.items():
                setattr(job, key, value)

    def add_file(self, job_id: str, file: JobFile) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is not None:
                job.files.append(file)


registry = JobRegistry()

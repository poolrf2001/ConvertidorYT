"""SQLite-backed job registry.

Persists conversion jobs so restarts don't lose history.
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Literal

JobStatus = Literal["queued", "running", "done", "error"]

DB_PATH = Path(os.environ.get("DB_PATH", "./jobs.db")).resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_ALLOWED_UPDATE_FIELDS = {"status", "progress", "current_title", "error"}


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
    created_at: float = 0.0
    files: list[JobFile] = field(default_factory=list)


class JobRegistry:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    quality TEXT NOT NULL,
                    playlist INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL NOT NULL DEFAULT 0,
                    current_title TEXT NOT NULL DEFAULT '',
                    error TEXT,
                    created_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS job_files (
                    job_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    PRIMARY KEY (job_id, idx),
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
                """
            )

    def create(self, url: str, quality: str, playlist: bool) -> Job:
        job = Job(
            id=uuid.uuid4().hex,
            url=url,
            quality=quality,
            playlist=playlist,
            created_at=time.time(),
        )
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO jobs (id,url,quality,playlist,status,progress,current_title,error,created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    job.id,
                    job.url,
                    job.quality,
                    int(job.playlist),
                    job.status,
                    job.progress,
                    job.current_title,
                    job.error,
                    job.created_at,
                ),
            )
        return job

    def get(self, job_id: str) -> Job | None:
        with self._conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None:
                return None
            files = c.execute(
                "SELECT idx, title, path, size_bytes FROM job_files WHERE job_id=? ORDER BY idx",
                (job_id,),
            ).fetchall()

        return Job(
            id=row["id"],
            url=row["url"],
            quality=row["quality"],
            playlist=bool(row["playlist"]),
            status=row["status"],
            progress=row["progress"],
            current_title=row["current_title"],
            error=row["error"],
            created_at=row["created_at"],
            files=[
                JobFile(
                    index=f["idx"],
                    title=f["title"],
                    path=f["path"],
                    size_bytes=f["size_bytes"],
                )
                for f in files
            ],
        )

    def update(self, job_id: str, **fields) -> None:
        fields = {k: v for k, v in fields.items() if k in _ALLOWED_UPDATE_FIELDS}
        if not fields:
            return
        cols = ", ".join(f"{k}=?" for k in fields)
        values = list(fields.values())
        with self._lock, self._conn() as c:
            c.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*values, job_id))

    def add_file(self, job_id: str, file: JobFile) -> None:
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO job_files (job_id, idx, title, path, size_bytes)"
                " VALUES (?,?,?,?,?)",
                (job_id, file.index, file.title, file.path, file.size_bytes),
            )

    def ids_older_than(self, age_seconds: float) -> list[str]:
        cutoff = time.time() - age_seconds
        with self._conn() as c:
            rows = c.execute(
                "SELECT id FROM jobs WHERE created_at < ?", (cutoff,)
            ).fetchall()
        return [r["id"] for r in rows]

    def delete(self, job_ids: Iterable[str]) -> None:
        ids = list(job_ids)
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with self._lock, self._conn() as c:
            c.execute(f"DELETE FROM jobs WHERE id IN ({placeholders})", ids)


registry = JobRegistry()

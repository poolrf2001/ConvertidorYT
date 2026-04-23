"""FastAPI entrypoint for the YouTube → MP3 converter."""

import asyncio
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from converter import DOWNLOAD_DIR, run_conversion
from jobs import registry

CLEANUP_INTERVAL_SECONDS = int(os.environ.get("CLEANUP_INTERVAL_SECONDS", "3600"))
JOB_RETENTION_SECONDS = int(os.environ.get("JOB_RETENTION_SECONDS", str(24 * 3600)))


async def _cleanup_loop() -> None:
    while True:
        try:
            old_ids = registry.ids_older_than(JOB_RETENTION_SECONDS)
            for jid in old_ids:
                job_dir = DOWNLOAD_DIR / jid
                if job_dir.exists():
                    shutil.rmtree(job_dir, ignore_errors=True)
            registry.delete(old_ids)
        except Exception:
            pass
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        task.cancel()


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ConvertidorYT", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


Quality = Literal["128", "192", "320"]


class ConvertRequest(BaseModel):
    url: HttpUrl
    quality: Quality = "192"
    playlist: bool = False


class ConvertResponse(BaseModel):
    job_id: str


class JobFileOut(BaseModel):
    index: int
    title: str
    size_bytes: int


class JobOut(BaseModel):
    id: str
    status: str
    progress: float
    current_title: str
    error: str | None = None
    files: list[JobFileOut] = Field(default_factory=list)


@app.post("/api/convert", response_model=ConvertResponse)
@limiter.limit("10/minute")
def start_conversion(
    request: Request, req: ConvertRequest, background: BackgroundTasks
) -> ConvertResponse:
    job = registry.create(str(req.url), req.quality, req.playlist)
    background.add_task(run_conversion, job.id, str(req.url), req.quality, req.playlist)
    return ConvertResponse(job_id=job.id)


@app.get("/api/jobs/{job_id}", response_model=JobOut)
@limiter.limit("120/minute")
def job_status(request: Request, job_id: str) -> JobOut:
    job = registry.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return JobOut(
        id=job.id,
        status=job.status,
        progress=job.progress,
        current_title=job.current_title,
        error=job.error,
        files=[
            JobFileOut(index=f.index, title=f.title, size_bytes=f.size_bytes)
            for f in job.files
        ],
    )


@app.get("/api/download/{job_id}/{file_index}")
@limiter.limit("60/minute")
def download_file(request: Request, job_id: str, file_index: int) -> FileResponse:
    job = registry.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    matches = [f for f in job.files if f.index == file_index]
    if not matches:
        raise HTTPException(404, "File not ready or does not exist")
    file = matches[0]
    path = Path(file.path)
    if not path.exists():
        raise HTTPException(410, "File no longer available")
    return FileResponse(
        path=path,
        media_type="audio/mpeg",
        filename=f"{file.title}.mp3",
    )


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}

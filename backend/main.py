"""FastAPI entrypoint for the YouTube → MP3 converter."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl

from converter import run_conversion
from jobs import registry

app = FastAPI(title="ConvertidorYT", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
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
def start_conversion(req: ConvertRequest, background: BackgroundTasks) -> ConvertResponse:
    job = registry.create(str(req.url), req.quality, req.playlist)
    background.add_task(run_conversion, job.id, str(req.url), req.quality, req.playlist)
    return ConvertResponse(job_id=job.id)


@app.get("/api/jobs/{job_id}", response_model=JobOut)
def job_status(job_id: str) -> JobOut:
    job = registry.get(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return JobOut(
        id=job.id,
        status=job.status,
        progress=job.progress,
        current_title=job.current_title,
        error=job.error,
        files=[JobFileOut(index=f.index, title=f.title, size_bytes=f.size_bytes) for f in job.files],
    )


@app.get("/api/download/{job_id}/{file_index}")
def download_file(job_id: str, file_index: int) -> FileResponse:
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

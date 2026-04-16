"""
Autopply — FastAPI web server.
"""

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()  # load .env if present

import db
import fetcher
import ai_engine
from config import MIN_SCORE_THRESHOLD, PAGE_SIZE, SCORE_BATCH_SIZE, USER_PROFILE, JOB_SOURCES

app = FastAPI(title="Autopply")

STATIC = Path(__file__).parent / "static"
RESUME_PATH = Path(__file__).parent / "resume.md"


@app.on_event("startup")
def startup():
    db.init_db()


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/")
def serve_dashboard():
    return FileResponse(STATIC / "index.html")


# ─── Stats ────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    return db.get_stats()


# ─── Jobs ─────────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
def list_jobs(status: str = "scored", min_score: int = 0, limit: int = PAGE_SIZE):
    return db.get_jobs(status=status, min_score=min_score, limit=limit)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ─── Actions ──────────────────────────────────────────────────────────────────

class ActionPayload(BaseModel):
    action: str  # "apply" | "skip" | "maybe" | "reset"


STATUS_MAP = {
    "apply": "applied",
    "skip": "skipped",
    "maybe": "maybe",
    "reset": "scored",
}


@app.post("/api/jobs/{job_id}/action")
def job_action(job_id: str, payload: ActionPayload):
    if payload.action not in STATUS_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown action: {payload.action}")
    db.set_job_status(job_id, STATUS_MAP[payload.action])
    return {"status": "ok", "new_status": STATUS_MAP[payload.action]}


# ─── Resume Tailoring ─────────────────────────────────────────────────────────

@app.post("/api/jobs/{job_id}/tailor")
def tailor_resume(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = db.get_tailored_resume(job_id)
    if existing:
        return {"tailored_resume": existing}
    tailored = ai_engine.tailor_resume(job)
    db.save_tailored_resume(job_id, tailored)
    return {"tailored_resume": tailored}


# ─── Settings ────────────────────────────────────────────────────────────────

@app.get("/api/settings")
def get_settings():
    default_resume = ""
    if RESUME_PATH.exists():
        default_resume = RESUME_PATH.read_text()

    return {
        "profile": json.loads(db.get_setting("profile") or json.dumps(USER_PROFILE)),
        "resume": db.get_setting("resume") or default_resume,
        "job_sources": json.loads(db.get_setting("job_sources") or json.dumps(JOB_SOURCES)),
    }


class SettingsPayload(BaseModel):
    profile: dict[str, Any] | None = None
    resume: str | None = None
    job_sources: list[dict] | None = None


@app.post("/api/settings")
def save_settings(payload: SettingsPayload):
    if payload.profile is not None:
        db.set_setting("profile", json.dumps(payload.profile))
    if payload.resume is not None:
        db.set_setting("resume", payload.resume)
    if payload.job_sources is not None:
        db.set_setting("job_sources", json.dumps(payload.job_sources))
    return {"status": "ok"}


# ─── Refresh ─────────────────────────────────────────────────────────────────

@app.post("/api/refresh")
def refresh():
    # Use job sources from DB settings if available
    sources_raw = db.get_setting("job_sources")
    if sources_raw:
        import config as _cfg
        _cfg.JOB_SOURCES = json.loads(sources_raw)

    new_jobs = fetcher.fetch_all()
    scored = ai_engine.score_unscored(limit=SCORE_BATCH_SIZE)
    return {"new_jobs": new_jobs, "scored": scored}


@app.post("/api/score-pending")
def score_pending():
    scored = ai_engine.score_unscored(limit=SCORE_BATCH_SIZE)
    return {"scored": scored}

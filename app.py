"""
Job Hunt AI — FastAPI web server.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import db
import fetcher
import ai_engine
from config import MIN_SCORE_THRESHOLD, PAGE_SIZE, SCORE_BATCH_SIZE

app = FastAPI(title="Job Hunt AI")

STATIC = Path(__file__).parent / "static"


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
    new_status = STATUS_MAP[payload.action]
    db.set_job_status(job_id, new_status)
    return {"status": "ok", "new_status": new_status}


# ─── Resume Tailoring ─────────────────────────────────────────────────────────

@app.post("/api/jobs/{job_id}/tailor")
def tailor_resume(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Return cached tailored resume if already generated
    existing = db.get_tailored_resume(job_id)
    if existing:
        return {"tailored_resume": existing}

    tailored = ai_engine.tailor_resume(job)
    db.save_tailored_resume(job_id, tailored)
    return {"tailored_resume": tailored}


@app.get("/api/jobs/{job_id}/tailored-resume")
def get_tailored_resume(job_id: str):
    text = db.get_tailored_resume(job_id)
    if text is None:
        raise HTTPException(status_code=404, detail="Not yet generated")
    return {"tailored_resume": text}


# ─── Refresh (fetch + score) ─────────────────────────────────────────────────

@app.post("/api/refresh")
def refresh():
    """Fetch new jobs from all sources, then score them."""
    print("Fetching new jobs...")
    new_jobs = fetcher.fetch_all()
    print(f"Scoring up to {SCORE_BATCH_SIZE} new jobs...")
    scored = ai_engine.score_unscored(limit=SCORE_BATCH_SIZE)
    return {"new_jobs": new_jobs, "scored": scored}


@app.post("/api/score-pending")
def score_pending():
    """Score unscored jobs without fetching new ones."""
    scored = ai_engine.score_unscored(limit=SCORE_BATCH_SIZE)
    return {"scored": scored}

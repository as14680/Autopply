import os
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path

# Use DATA_DIR env var when set (e.g. a Railway persistent volume at /data).
# Falls back to the directory containing this file for local development.
_data_dir = Path(os.environ.get("DATA_DIR", Path(__file__).parent))
_data_dir.mkdir(parents=True, exist_ok=True)
DB_PATH = _data_dir / "jobs.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id          TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    title       TEXT NOT NULL,
    company     TEXT,
    location    TEXT,
    url         TEXT UNIQUE NOT NULL,
    description TEXT,
    posted_at   TEXT,
    fetched_at  TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'new',
    fit_score   INTEGER,
    analysis    TEXT,
    tailored_resume TEXT,
    notes       TEXT
);

CREATE TABLE IF NOT EXISTS activity_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id    TEXT,
    action    TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    details   TEXT
);
"""


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.executescript(_SCHEMA)


def get_stats() -> dict:
    with get_db() as db:
        row = db.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(status = 'new') AS unscored,
                SUM(status = 'scored') AS to_review,
                SUM(status = 'applied') AS applied,
                SUM(status = 'maybe') AS maybe,
                SUM(status = 'skipped') AS skipped,
                ROUND(AVG(CASE WHEN fit_score IS NOT NULL THEN fit_score END), 1) AS avg_score
            FROM jobs
        """).fetchone()
        return dict(row)


def get_jobs(status: str = "scored", min_score: int = 0, limit: int = 50) -> list[dict]:
    with get_db() as db:
        if status == "all":
            rows = db.execute("""
                SELECT id, source, title, company, location, url,
                       posted_at, fetched_at, status, fit_score, analysis, notes
                FROM jobs
                WHERE (fit_score >= ? OR fit_score IS NULL)
                ORDER BY fit_score DESC NULLS LAST, fetched_at DESC
                LIMIT ?
            """, (min_score, limit)).fetchall()
        else:
            rows = db.execute("""
                SELECT id, source, title, company, location, url,
                       posted_at, fetched_at, status, fit_score, analysis, notes
                FROM jobs
                WHERE status = ?
                  AND (fit_score >= ? OR fit_score IS NULL)
                ORDER BY fit_score DESC NULLS LAST, fetched_at DESC
                LIMIT ?
            """, (status, min_score, limit)).fetchall()

    result = []
    for row in rows:
        job = dict(row)
        if job["analysis"]:
            job["analysis"] = json.loads(job["analysis"])
        result.append(job)
    return result


def get_job(job_id: str) -> dict | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        return None
    job = dict(row)
    if job["analysis"]:
        job["analysis"] = json.loads(job["analysis"])
    return job


def set_job_status(job_id: str, status: str) -> None:
    with get_db() as db:
        db.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        db.execute(
            "INSERT INTO activity_log (job_id, action) VALUES (?, ?)",
            (job_id, status),
        )


def save_analysis(job_id: str, score: int, analysis: dict) -> None:
    with get_db() as db:
        db.execute(
            "UPDATE jobs SET status = 'scored', fit_score = ?, analysis = ? WHERE id = ?",
            (score, json.dumps(analysis), job_id),
        )


def save_tailored_resume(job_id: str, text: str) -> None:
    with get_db() as db:
        db.execute("UPDATE jobs SET tailored_resume = ? WHERE id = ?", (text, job_id))


def get_tailored_resume(job_id: str) -> str | None:
    with get_db() as db:
        row = db.execute(
            "SELECT tailored_resume FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()
    return row["tailored_resume"] if row else None


def get_setting(key: str, default: str | None = None) -> str | None:
    with get_db() as db:
        row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )


def get_unscored_jobs(limit: int = 25) -> list[dict]:
    with get_db() as db:
        rows = db.execute("""
            SELECT id, title, company, location, source, description
            FROM jobs WHERE status = 'new'
            ORDER BY fetched_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]

"""
Job Fetcher — pulls listings from RSS feeds and stores new ones in the DB.
"""

import hashlib
import re
import sqlite3
from datetime import datetime, timezone

import feedparser

from config import JOB_SOURCES
from db import get_db, init_db


def _job_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:6000]


def _parse_date(entry) -> str:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        import email.utils
        parts = email.utils.parsedate(raw)
        if parts:
            return datetime(*parts[:6], tzinfo=timezone.utc).isoformat()
    except Exception:
        pass
    return datetime.now(timezone.utc).isoformat()


def _extract_company(entry) -> str:
    for field in ["author", "dc_creator"]:
        val = entry.get(field, "")
        if isinstance(val, dict):
            val = val.get("name", "")
        if val:
            return val.strip()
    title = entry.get("title", "")
    if " at " in title:
        return title.rsplit(" at ", 1)[-1].strip()
    if " - " in title:
        return title.rsplit(" - ", 1)[-1].strip()
    return "Unknown"


def _extract_location(entry) -> str:
    for field in ["location", "geo_location"]:
        val = entry.get(field, "")
        if val:
            return str(val).strip()
    return "Unknown"


def _extract_description(entry) -> str:
    # Try content blocks first (richer)
    content = entry.get("content", [])
    if content and isinstance(content, list):
        return _strip_html(content[0].get("value", ""))
    summary = entry.get("summary", "") or entry.get("description", "")
    return _strip_html(summary)


def fetch_source(source: dict) -> list[dict]:
    try:
        feed = feedparser.parse(source["url"])
    except Exception as e:
        print(f"  [error] {source['name']}: {e}")
        return []

    jobs = []
    for entry in feed.entries:
        url = entry.get("link") or entry.get("id", "")
        if not url:
            continue
        jobs.append({
            "id": _job_id(url),
            "source": source["name"],
            "title": (entry.get("title") or "Untitled").strip(),
            "company": _extract_company(entry),
            "location": _extract_location(entry),
            "url": url,
            "description": _extract_description(entry),
            "posted_at": _parse_date(entry),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        })
    return jobs


def save_jobs(jobs: list[dict]) -> int:
    new_count = 0
    with get_db() as db:
        for job in jobs:
            try:
                db.execute("""
                    INSERT INTO jobs
                        (id, source, title, company, location, url,
                         description, posted_at, fetched_at, status)
                    VALUES
                        (:id, :source, :title, :company, :location, :url,
                         :description, :posted_at, :fetched_at, 'new')
                """, job)
                new_count += 1
            except sqlite3.IntegrityError:
                pass  # duplicate URL — skip silently
    return new_count


def fetch_all() -> int:
    init_db()
    total = 0
    for source in JOB_SOURCES:
        if not source.get("active", True):
            continue
        print(f"  Fetching {source['name']}...")
        jobs = fetch_source(source)
        new = save_jobs(jobs)
        total += new
        print(f"    {len(jobs)} found, {new} new")
    return total

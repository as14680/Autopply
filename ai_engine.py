"""
AI Engine — Claude-powered job scoring, resume tailoring, and gap analysis.

Uses:
  - claude-opus-4-6 for all analysis
  - Prompt caching on system prompt + resume/profile (stable across all jobs)
  - Tool use with forced tool call for reliable structured scoring output
  - Streaming for resume tailoring (long output)
"""

import json
from pathlib import Path

import anthropic

from config import USER_PROFILE
from db import get_unscored_jobs, save_analysis

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

RESUME_PATH = Path(__file__).parent / "resume.md"
MODEL = "claude-opus-4-6"


# ─── Tool Schema for Structured Scoring ──────────────────────────────────────

_SCORE_TOOL = {
    "name": "record_job_analysis",
    "description": "Record the complete structured analysis of a job posting.",
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "score", "score_rationale", "strong_matches", "gaps",
            "networking_targets", "recommendation", "key_selling_points",
            "red_flags", "cover_letter_hook",
        ],
        "properties": {
            "score": {
                "type": "integer",
                "description": "Fit score 0–100. 80+ = strong match. 60–79 = worth applying with gaps. <60 = significant mismatch.",
            },
            "score_rationale": {
                "type": "string",
                "description": "2–3 sentence explanation of the score.",
            },
            "strong_matches": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Skills or experiences that directly match the role.",
            },
            "gaps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["gap", "severity", "how_to_address"],
                    "properties": {
                        "gap": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["minor", "moderate", "major"],
                        },
                        "how_to_address": {"type": "string"},
                    },
                },
                "description": "Missing skills or experience with severity and how to address each.",
            },
            "networking_targets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["role", "why"],
                    "properties": {
                        "role": {"type": "string"},
                        "why": {"type": "string"},
                    },
                },
                "description": "Types of people to connect with at this company.",
            },
            "recommendation": {
                "type": "string",
                "enum": ["strong_apply", "apply", "maybe", "skip"],
                "description": "Application recommendation.",
            },
            "key_selling_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "What to emphasize in the application.",
            },
            "red_flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Concerns about the role or company.",
            },
            "cover_letter_hook": {
                "type": "string",
                "description": "One compelling opening sentence for a cover letter.",
            },
        },
    },
}

_SYSTEM_PROMPT = """\
You are an expert career coach and senior recruiter with 15 years of experience \
placing engineers at top tech companies. Your role is to analyze job postings \
against a candidate's profile and provide brutally honest, actionable assessments.

Scoring guide:
- 85–100: Exceptional fit — candidate clearly exceeds most requirements
- 70–84: Strong fit — meets core requirements, minor gaps
- 55–69: Moderate fit — worth applying, some gaps to address
- 40–54: Weak fit — significant gaps, long shot
- <40: Poor fit — major mismatch, skip unless highly motivated

Be honest. Do not inflate scores to be encouraging. A realistic 65 helps more \
than a false 85."""


def _load_resume() -> str:
    from db import get_setting
    stored = get_setting("resume")
    if stored:
        return stored
    try:
        return RESUME_PATH.read_text()
    except FileNotFoundError:
        return "(Resume not found — please add your resume in Settings)"


def _load_profile() -> dict:
    from db import get_setting
    stored = get_setting("profile")
    if stored:
        return json.loads(stored)
    return USER_PROFILE


def _profile_block() -> str:
    return f"## Candidate Profile\n\n{json.dumps(_load_profile(), indent=2)}\n\n## Resume\n\n{_load_resume()}"


# ─── Scoring ─────────────────────────────────────────────────────────────────

def score_job(job: dict) -> dict:
    """
    Score a single job and return the analysis dict.

    Caches system prompt + profile/resume across calls (stable prefix).
    """
    profile_and_resume = _profile_block()
    job_text = (
        f"**Title:** {job.get('title', 'N/A')}\n"
        f"**Company:** {job.get('company', 'N/A')}\n"
        f"**Location:** {job.get('location', 'N/A')}\n"
        f"**Source:** {job.get('source', 'N/A')}\n\n"
        f"**Description:**\n{(job.get('description') or '')[:5000]}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # stable — cache it
            }
        ],
        tools=[_SCORE_TOOL],
        tool_choice={"type": "tool", "name": "record_job_analysis"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": profile_and_resume,
                        "cache_control": {"type": "ephemeral"},  # stable per-session — cache
                    },
                    {
                        "type": "text",
                        "text": f"## Job to Analyze\n\n{job_text}\n\nAnalyze this job and call record_job_analysis.",
                    },
                ],
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    # Fallback if tool call not found (shouldn't happen with forced tool_choice)
    return {
        "score": 0,
        "score_rationale": "Analysis failed.",
        "strong_matches": [],
        "gaps": [],
        "networking_targets": [],
        "recommendation": "skip",
        "key_selling_points": [],
        "red_flags": ["Analysis failed"],
        "cover_letter_hook": "",
    }


def score_unscored(limit: int = 25) -> int:
    """Score all unscored jobs up to `limit`. Returns count scored."""
    jobs = get_unscored_jobs(limit)
    if not jobs:
        return 0

    print(f"  Scoring {len(jobs)} jobs...")
    scored = 0
    for job in jobs:
        try:
            analysis = score_job(job)
            save_analysis(job["id"], analysis["score"], analysis)
            scored += 1
            rec = analysis.get("recommendation", "?")
            print(f"  [{analysis['score']:3d}] {job['title'][:50]} @ {job.get('company','?')} ({rec})")
        except Exception as e:
            print(f"  [error] {job['id']}: {e}")

    return scored


# ─── Resume Tailoring ─────────────────────────────────────────────────────────

def tailor_resume(job: dict) -> str:
    """
    Generate a tailored version of the resume for a specific job.
    Uses streaming for long output.
    """
    resume = _load_resume()
    description = (job.get("description") or "")[:4000]

    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"## My Base Resume\n\n{resume}",
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": f"""\
## Job I'm Applying For

**Title:** {job.get('title', 'N/A')}
**Company:** {job.get('company', 'N/A')}

**Description:**
{description}

## Task

Tailor my resume for this specific role. Rules:
1. Only use information that already exists in my resume — do not fabricate
2. Reorder bullet points to lead with most relevant achievements first
3. Mirror the job's terminology and keywords where natural
4. Keep the same overall format and similar length
5. Add a "TAILORING NOTES" section at the end explaining what you changed and why

Return the full tailored resume in markdown format.""",
                    },
                ],
            }
        ],
    ) as stream:
        final = stream.get_final_message()

    for block in final.content:
        if block.type == "text":
            return block.text

    return "Tailoring failed."

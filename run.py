#!/usr/bin/env python3
"""
Job Hunt AI — Entry point.

Usage:
  python run.py              # start dashboard (default)
  python run.py serve        # start dashboard
  python run.py fetch        # fetch new jobs from RSS feeds
  python run.py score        # score unscored jobs with Claude
  python run.py refresh      # fetch + score (full morning refresh)
"""

import os
import sys

# Add job_hunt directory to path so imports resolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Auto-load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _check_api_key():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set.")
        print("Run:  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)


def cmd_serve():
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting Autopply at http://localhost:{port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)


def cmd_fetch():
    import fetcher
    print("Fetching jobs from all sources...")
    n = fetcher.fetch_all()
    print(f"Done — {n} new jobs added.")


def cmd_score():
    _check_api_key()
    import ai_engine
    from config import SCORE_BATCH_SIZE
    print(f"Scoring up to {SCORE_BATCH_SIZE} unscored jobs...")
    n = ai_engine.score_unscored(SCORE_BATCH_SIZE)
    print(f"Done — {n} jobs scored.")


def cmd_refresh():
    print("=== Morning Refresh ===")
    cmd_fetch()
    _check_api_key()
    import ai_engine
    from config import SCORE_BATCH_SIZE
    print(f"\nScoring up to {SCORE_BATCH_SIZE} new jobs...")
    n = ai_engine.score_unscored(SCORE_BATCH_SIZE)
    print(f"Done — {n} jobs scored.")
    print("\nOpen http://localhost:8000 to review your brief.")


COMMANDS = {
    "serve":   cmd_serve,
    "fetch":   cmd_fetch,
    "score":   cmd_score,
    "refresh": cmd_refresh,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "serve"
    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[cmd]()

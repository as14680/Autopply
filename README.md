# Autopply

An AI-powered job hunting system that turns your morning job search into a single decision loop: **Apply, Maybe, or Skip.**

Every morning it fetches new listings, scores each role for fit (0–100), tailors your resume, identifies gaps, and surfaces networking targets — all before you open your laptop.

---

## What it does

| Feature | Detail |
|---|---|
| **Job fetching** | Pulls listings from RSS feeds (Indeed, We Work Remotely, Remote.co, Remotive, and any custom source) |
| **Fit scoring** | Claude analyzes each job against your resume and profile, returns a 0–100 score with rationale |
| **Gap analysis** | Identifies missing skills with severity (minor / moderate / major) and how to address each |
| **Resume tailoring** | Rewrites your resume for a specific role — same facts, reordered and reworded to match the job |
| **Networking targets** | Suggests which types of people at the company to connect with before applying |
| **Cover letter hook** | One compelling opening sentence, ready to use |
| **Decision dashboard** | Morning briefing UI — sorted by fit score, one-click Apply / Maybe / Skip |

---

## Screenshots

```
Morning Brief — Wednesday, April 16, 2026
12 new roles · Avg fit: 74 · 3 applied

[93] Senior Engineer @ Stripe        Remote · Posted 2h ago
     ✓ Python  ✓ Distributed systems  ✓ Fintech
     [Apply]  [Maybe]  [Skip]  [Tailor Resume]  [View Posting →]

[87] Staff Engineer @ Anthropic       Remote · Posted 5h ago
     ✓ Python  ✓ APIs  ✓ AI/ML
     [Apply]  [Maybe]  [Skip]  [Tailor Resume]  [View Posting →]
```

---

## Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Setup (Local)

**1. Clone the repo**

```bash
git clone https://github.com/as14680/Autopply.git
cd Autopply
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Set your API key**

```bash
cp .env.example .env
# open .env and add your Anthropic API key
```

Or just export it inline:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**4. Start the server**

```bash
python run.py serve
```

Open **http://localhost:8000** and go to **Settings** to fill in your profile, paste your resume, and configure job sources — no file editing required.

---

## Deploy to Railway (free tier)

Get a public URL in about 2 minutes:

1. Push this repo to GitHub (already done if you cloned it)
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo → select **Autopply**
3. Add an environment variable: `ANTHROPIC_API_KEY` = your key
4. Railway auto-detects the `Dockerfile` and deploys — you get a public URL like `https://autopply-production.up.railway.app`

The `railway.toml` and `Dockerfile` are already included — no extra config needed.

---

## Deploy to Render

1. Go to [render.com](https://render.com) → New Web Service → connect your GitHub repo
2. Set **Runtime** to Docker (uses the included `Dockerfile`)
3. Add environment variable: `ANTHROPIC_API_KEY` = your key
4. Deploy

---

## Deploy to Heroku

```bash
heroku create autopply
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
git push heroku main
heroku open
```

The `Procfile` is already included.

---

## Daily usage

**Full morning refresh** (fetch new jobs + score them):

```bash
python run.py refresh
```

**Open the dashboard:**

```bash
python run.py serve
# → http://localhost:8000
```

**Other commands:**

```bash
python run.py fetch    # fetch new jobs from RSS feeds only
python run.py score    # score unscored jobs only (no fetch)
```

---

## How scoring works

Each job is analyzed by `claude-opus-4-6` using your resume and profile as context. The model is forced to return a structured JSON object via tool use, so scores are always consistent and parseable.

**Score guide:**
- **85–100** — Exceptional fit, you exceed most requirements
- **70–84** — Strong fit, worth applying with confidence
- **55–69** — Moderate fit, apply but address the gaps
- **40–54** — Weak fit, long shot
- **< 40** — Skip unless you're highly motivated

Your resume and profile are **prompt-cached** on the first scoring call each session, so subsequent jobs in the same batch cost significantly less to score.

---

## Project structure

```
Autopply/
├── config.py          # Default profile/sources (overridden by DB settings)
├── resume.md          # Default resume (overridden by Settings page)
├── ai_engine.py       # Claude API — scoring, tailoring
├── app.py             # FastAPI web server and API endpoints
├── db.py              # SQLite database layer (jobs + settings)
├── fetcher.py         # RSS feed parser and job storage
├── run.py             # CLI entry point
├── Dockerfile         # Docker image for deployment
├── Procfile           # Heroku process declaration
├── railway.toml       # Railway deployment config
├── requirements.txt
└── static/
    └── index.html     # Dashboard SPA (Morning Brief / History / Settings)
```

---

## Automating the morning refresh

To have new jobs ready before you wake up, add a cron job:

```bash
# Run refresh at 6 AM every day
crontab -e

0 6 * * * cd /path/to/Autopply && source .env && python run.py refresh
```

Then just open the dashboard when you're ready.

---

## Adding job sources

Go to **Settings → Job Sources** in the dashboard and paste any RSS feed URL. No file editing required.

Common sources to add:

```
https://hnrss.org/jobs            (Hacker News Jobs)
https://remotive.com/remote-jobs/feed
https://weworkremotely.com/jobs.rss
```

Many job boards (Greenhouse, Lever, Workable) expose company-specific RSS feeds — search for `site:jobs.lever.co/yourcompany RSS` or check the job board's documentation.

---

## Tech stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — web server
- **[Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)** — Claude API (claude-opus-4-6)
- **[feedparser](https://feedparser.readthedocs.io/)** — RSS parsing
- **SQLite** — local job storage
- Vanilla HTML/CSS/JS dashboard (no build step)

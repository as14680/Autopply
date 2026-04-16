# Autopply

An AI-powered job hunting system that turns your morning job search into a single decision loop: **Apply, Maybe, or Skip.**

Every morning it fetches new listings from RSS feeds, scores each role for fit (0–100) against your resume, tailors your resume per role, identifies skill gaps, and surfaces networking targets — all from a browser dashboard. No spreadsheets. No file editing.

---

## What it does

| Feature | Detail |
|---|---|
| **Job fetching** | Pulls listings from RSS feeds (Indeed, We Work Remotely, Remote.co, Remotive, and any custom source you add) |
| **Fit scoring** | Claude analyzes each job against your resume and profile, returns a 0–100 score with detailed rationale |
| **Gap analysis** | Identifies missing skills with severity (minor / moderate / major) and how to address each |
| **Resume tailoring** | Rewrites your resume for a specific role — same facts, reordered and reworded to match the job |
| **Networking targets** | Suggests which types of people at the company to connect with before applying |
| **Cover letter hook** | One compelling opening sentence, ready to paste |
| **Decision dashboard** | Morning briefing UI — sorted by fit score, one-click Apply / Maybe / Skip |
| **History tracking** | Review applied, skipped, and maybe jobs; reset any decision at any time |

---

## Dashboard

The app has three pages accessible from the sidebar:

- **Morning Brief** — today's scored jobs sorted by fit score. Filter by To Review / Maybe / All. Click any card to expand full analysis, gaps, networking targets, and tailored resume.
- **History** — Applied / Maybe / Skipped tabs. Reset any job back to the queue.
- **Settings** — Edit your profile, paste your resume, and manage job sources entirely in the browser. No file editing required.

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
# open .env and set ANTHROPIC_API_KEY=sk-ant-...
```

Or export it inline:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**4. Start the server**

```bash
python run.py serve
```

Open **http://localhost:8000**, go to **Settings**, fill in your profile, paste your resume, and add job source URLs. Then hit **Refresh Jobs** on the Morning Brief page.

---

## First run walkthrough

1. Open `http://localhost:8000`
2. Click **Settings** in the sidebar
3. Fill in your name, title, years of experience, skills, target roles, and salary range
4. Paste your full resume in the Resume box
5. Add or enable job sources under Job Sources
6. Click **Save Settings**
7. Go back to **Morning Brief** and click **Refresh Jobs**
8. Wait ~30–60 seconds while Claude scores each job
9. Review your scored jobs — click any card to see the full analysis

---

## Daily usage

**Morning refresh from the browser:** click **Refresh Jobs** on the dashboard.

**Or from the terminal:**

```bash
python run.py refresh   # fetch new jobs + score them
python run.py fetch     # fetch only (no scoring)
python run.py score     # score unscored jobs only
python run.py serve     # start the dashboard server
```

**Automate with cron** (jobs ready when you wake up):

```bash
crontab -e
# Add:
0 6 * * * cd /path/to/Autopply && source .env && python run.py refresh
```

---

## Deploy to Railway (free tier)

Get a public URL in ~2 minutes:

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select **Autopply**
2. Add environment variable: `ANTHROPIC_API_KEY` = your key
3. Railway auto-detects the `Dockerfile` and deploys — you get a public URL like `https://autopply-production.up.railway.app`

The `railway.toml` and `Dockerfile` are already included.

---

## Deploy to Render

1. Go to [render.com](https://render.com) → **New Web Service** → connect your GitHub repo
2. Set Runtime to **Docker**
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

## How scoring works

Each job is analyzed by `claude-opus-4-6` using your resume and profile as context. The model is forced to return a structured JSON object via tool use — scores are always consistent and machine-readable.

**Score guide:**
- **85–100** — Exceptional fit, you exceed most requirements
- **70–84** — Strong fit, worth applying with confidence
- **55–69** — Moderate fit, apply but address the gaps
- **40–54** — Weak fit, long shot
- **< 40** — Skip unless highly motivated

Your resume and profile are **prompt-cached** on the first scoring call each session, so subsequent jobs in the same batch cost significantly less.

---

## Project structure

```
Autopply/
├── config.py          # Default profile/sources (overridden by Settings page)
├── resume.md          # Default resume (overridden by Settings page)
├── ai_engine.py       # Claude API — scoring and resume tailoring
├── app.py             # FastAPI web server and REST API
├── db.py              # SQLite layer (jobs + settings)
├── fetcher.py         # RSS feed parser and job ingestion
├── run.py             # CLI entry point
├── Dockerfile         # Docker image for cloud deployment
├── Procfile           # Heroku process declaration
├── railway.toml       # Railway deployment config
├── requirements.txt
└── static/
    └── index.html     # Single-page app (Morning Brief / History / Settings)
```

---

## Adding job sources

Go to **Settings → Job Sources** in the dashboard and paste any RSS feed URL.

Common sources:

```
https://hnrss.org/jobs
https://remotive.com/remote-jobs/feed
https://weworkremotely.com/jobs.rss
https://remote.co/remote-jobs/feed/
```

Many companies also expose role-specific RSS feeds via Greenhouse, Lever, or Workable — search `site:jobs.lever.co/companyname rss` to find them.

---

## Tech stack

- **[FastAPI](https://fastapi.tiangolo.com/)** — web server
- **[Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)** — Claude API (`claude-opus-4-6`) with tool use + prompt caching
- **[feedparser](https://feedparser.readthedocs.io/)** — RSS parsing
- **SQLite** — job storage and settings persistence
- Vanilla HTML/CSS/JS — no build step, no framework

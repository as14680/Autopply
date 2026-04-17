"""
Job Hunt AI — Configuration
Fill in your details before running.
"""

# ─── Your Profile ─────────────────────────────────────────────────────────────

USER_PROFILE = {
    "name": "Your Name",
    "current_title": "Software Engineer",
    "years_experience": 5,
    "skills": [
        "Python", "JavaScript", "React", "PostgreSQL", "AWS", "Docker"
    ],
    "target_roles": [
        "Senior Software Engineer",
        "Staff Software Engineer",
        "Engineering Manager",
    ],
    "preferred_locations": ["Remote", "San Francisco, CA", "New York, NY"],
    "salary_range": {"min": 150000, "max": 250000, "currency": "USD"},
    "preferred_industries": ["AI/ML", "Fintech", "SaaS", "Developer Tools"],
    "work_preference": "remote",  # "remote", "hybrid", or "onsite"
    "deal_breakers": [
        # Strings that make a job an automatic skip.
        # e.g. "requires clearance", "no remote", "unpaid"
    ],
    "priorities": [
        "technical growth",
        "compensation",
        "remote flexibility",
    ],
}

# ─── Job Sources (RSS feeds) ──────────────────────────────────────────────────

JOB_SOURCES = [
    # ── Product Management (active by default) ────────────────────────────────
    # Remotive — Product / PM roles
    {
        "name": "Remotive Product",
        "url": "https://remotive.com/remote-jobs/feed/product",
        "active": True,
    },
    # We Work Remotely — Management & Finance (PM, Operations, etc.)
    {
        "name": "WWR Management",
        "url": "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
        "active": True,
    },
    # Remote.co — Product Manager
    {
        "name": "Remote.co PM",
        "url": "https://remote.co/remote-jobs/product-manager/feed/",
        "active": True,
    },
    # Hacker News Jobs (broad — includes PM, eng, leadership)
    {
        "name": "HackerNews Jobs",
        "url": "https://hnrss.org/jobs",
        "active": True,
    },

    # ── Engineering (disabled by default — enable if needed) ─────────────────
    {
        "name": "Remotive Engineering",
        "url": "https://remotive.com/remote-jobs/feed/software-dev",
        "active": False,
    },
    {
        "name": "WWR Engineering",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "active": False,
    },

    # ── Indeed (blocks cloud IPs — only works when running locally) ───────────
    {
        "name": "Indeed",
        "url": "https://www.indeed.com/rss?q=senior+product+manager&l=remote&sort=date",
        "active": False,
    },
]

# ─── Dashboard Settings ───────────────────────────────────────────────────────

# Jobs per page on the dashboard
PAGE_SIZE = 50

# Only show jobs with at least this score in the "To Review" tab
MIN_SCORE_THRESHOLD = 45

# Score new jobs in batches of this size per refresh
SCORE_BATCH_SIZE = 25

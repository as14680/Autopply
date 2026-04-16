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
    # Indeed — customize the query string for your target role
    {
        "name": "Indeed",
        "url": "https://www.indeed.com/rss?q=senior+software+engineer&l=remote&sort=date",
        "active": True,
    },
    # We Work Remotely — Engineering & Code
    {
        "name": "WeWorkRemotely",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "active": True,
    },
    # Remote.co — Developer jobs
    {
        "name": "Remote.co",
        "url": "https://remote.co/remote-jobs/developer/feed/",
        "active": True,
    },
    # Remotive — Software Engineering
    {
        "name": "Remotive",
        "url": "https://remotive.com/remote-jobs/feed/software-dev",
        "active": True,
    },
    # Add your own sources:
    # {
    #     "name": "Custom",
    #     "url": "https://...",
    #     "active": True,
    # },
]

# ─── Dashboard Settings ───────────────────────────────────────────────────────

# Jobs per page on the dashboard
PAGE_SIZE = 50

# Only show jobs with at least this score in the "To Review" tab
MIN_SCORE_THRESHOLD = 45

# Score new jobs in batches of this size per refresh
SCORE_BATCH_SIZE = 25

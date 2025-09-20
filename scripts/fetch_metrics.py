import datetime
import json
import os

import requests

GH = os.environ.get("GH_TOKEN")
REPO = os.environ.get("REPO", "your-org/hallucination-detector")
headers = {"Authorization": f"Bearer {GH}"} if GH else {}


def gh(path, params=None):
    r = requests.get(
        f"https://api.github.com{path}", headers=headers, params=params or {}
    )
    r.raise_for_status()
    return r.json()


def stars(repo):
    return gh(f"/repos/{repo}")["stargazers_count"]


def merged_prs_7d(repo):
    date_from = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    q = f"repo:{repo} is:pr is:merged merged:>={date_from}"
    return gh("/search/issues", {"q": q})["total_count"]


def commit_streak_days(repo):
    # simple proxy: days since last date without commit, capped at 30 by default
    events = gh(f"/repos/{repo}/commits", {"per_page": 100})
    dates = sorted({e["commit"]["author"]["date"][:10] for e in events}, reverse=True)
    from datetime import date, timedelta

    streak = 0
    d = date.today()
    while d.isoformat() in dates:
        streak += 1
        d -= timedelta(days=1)
    return streak


data = {
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "repo": REPO,
    "stars": stars(REPO),
    "merged_prs_week": merged_prs_7d(REPO),
    "commit_streak_days": commit_streak_days(REPO),
    # Business KPIs as placeholders to be filled by your pipeline or env variables
    "errors_prevented_month": None,
    "false_positive_rate": None,
    "mttr_minutes": None,
    "money_saved_usd_month": None,
    "customers_live": None,
    "uptime_pct": None,
}

os.makedirs("site/data", exist_ok=True)
with open("site/data/metrics.json", "w") as f:
    json.dump(data, f, indent=2)
print("Wrote site/data/metrics.json")

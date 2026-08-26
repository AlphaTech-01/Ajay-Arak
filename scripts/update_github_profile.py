#!/usr/bin/env python3
import html
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "AlphaTech-01")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

def api(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "github-profile-readme-updater",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)

def esc(value):
    return html.escape(str(value), quote=True)

def metric(x, label, value):
    return (
        f'<text x="{x}" y="122" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">{esc(label)}</text>'
        f'<text x="{x}" y="154" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="28" font-weight="700">{value}</text>'
    )

def shorten(text, limit=82):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit - 1] + "…"

user = api(f"/users/{USERNAME}")
repos = api(f"/users/{USERNAME}/repos?per_page=100&sort=updated")
events = api(f"/users/{USERNAME}/events/public?per_page=10")

public_repos = user.get("public_repos", 0)
followers = user.get("followers", 0)
following = user.get("following", 0)
owned_repos = [repo for repo in repos if not repo.get("fork", False)]
stars = sum(repo.get("stargazers_count", 0) for repo in owned_repos)
forks = sum(repo.get("forks_count", 0) for repo in owned_repos)
updated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

stats = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="210" viewBox="0 0 900 210">
<rect width="900" height="210" rx="14" fill="#0d1117"/>
<text x="40" y="42" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="22" font-weight="700">GitHub Snapshot</text>
<text x="40" y="68" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">Live public GitHub data · updated {updated}</text>
{metric(40, "Repositories", public_repos)}
{metric(210, "Followers", followers)}
{metric(380, "Stars received", stars)}
{metric(550, "Forks received", forks)}
{metric(720, "Following", following)}
<text x="40" y="188" fill="#8b949e" font-family="Arial,sans-serif" font-size="11">Source: GitHub REST API · public profile and repository data</text>
</svg>"""

(ASSETS / "github-stats.svg").write_text(stats, encoding="utf-8")

def event_text(event):
    event_type = event.get("type", "")
    repo = event.get("repo", {}).get("name", "")
    payload = event.get("payload", {})
    if event_type == "PushEvent":
        count = len(payload.get("commits", []))
        return f"Pushed {count} commit{'s' if count != 1 else ''} to {repo}"
    if event_type == "CreateEvent":
        return f"Created {payload.get('ref_type', 'resource')} in {repo}"
    if event_type == "PullRequestEvent":
        return f"{payload.get('action', 'Updated').title()} pull request in {repo}"
    if event_type == "IssuesEvent":
        return f"{payload.get('action', 'Updated').title()} issue in {repo}"
    if event_type == "IssueCommentEvent":
        return f"Commented on an issue in {repo}"
    if event_type == "WatchEvent":
        return f"Starred {repo}"
    if event_type == "ForkEvent":
        return f"Forked {repo}"
    if event_type == "ReleaseEvent":
        return f"Published a release in {repo}"
    return f"{event_type.replace('Event', '')} in {repo}".strip()

items = []
for event in events[:6]:
    if event.get("repo", {}).get("name"):
        items.append((event.get("created_at", "")[:10], event_text(event)))

if not items:
    items = [("", "No recent public activity available.")]

rows = []
for index, (date, text) in enumerate(items):
    y = 108 + index * 24
    rows.append(f'<text x="40" y="{y}" fill="#8b949e" font-family="Arial,sans-serif" font-size="12">{esc(date)}</text>')
    rows.append(f'<text x="130" y="{y}" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="12">{esc(shorten(text))}</text>')

activity = f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="290" viewBox="0 0 900 290">
<rect width="900" height="290" rx="14" fill="#0d1117"/>
<text x="40" y="42" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="22" font-weight="700">Recent GitHub Activity</text>
<text x="40" y="68" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">Latest public events · refreshed {updated}</text>
{''.join(rows)}
<text x="40" y="268" fill="#58a6ff" font-family="Arial,sans-serif" font-size="12">View full activity → github.com/{esc(USERNAME)}?tab=activity</text>
</svg>"""

(ASSETS / "github-activity.svg").write_text(activity, encoding="utf-8")

"""Who uses Timeline, read from GitHub: the repo's stars, and the people whose
files embed the wave or run the Action.

GitHub's code search only answers with a token, so without one the users come
back as None and the site leaves that row out. Code search sees default branches
only, and a file that changed in the last hours may not be indexed yet.
"""

import json
import urllib.parse
import urllib.request

REPO = "PasinduSuraweera/timeline"
# What a file has to contain to count as using Timeline: the hosted image, or the Action.
SEARCHES = ('"timeline-readme.vercel.app"', '"PasinduSuraweera/timeline-action"')
# Our own repos and copies of them mention both strings without using the wave.
OWN_REPOS = {"timeline", "timeline-action"}
# Profiles code search has missed. Each is still checked: it counts only while
# that profile README contains the wave or the Action.
KNOWN = ("PasinduSuraweera", "Dippy2003")
MARKERS = ("timeline-readme.vercel.app", "PasinduSuraweera/timeline-action")


def _get(url, token, timeout=8):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "timeline-stats",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _get_text(url, token, timeout=8):
    headers = {"Accept": "application/vnd.github.raw+json", "User-Agent": "timeline-stats",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def wears_wave(login, token):
    """True if login's profile README embeds the wave or runs the Action."""
    try:
        text = _get_text(f"https://api.github.com/repos/{login}/{login}/readme", token)
    except Exception:
        return False
    return any(m in text for m in MARKERS)


def stars(token=""):
    """The repo's star count, or None if GitHub could not be reached."""
    try:
        return int(_get(f"https://api.github.com/repos/{REPO}", token)["stargazers_count"])
    except Exception:
        return None


def users_from_items(items):
    """Distinct people behind a list of code search hits, in the order first seen.

    Leaves out forks and Timeline's own repos, since those mention Timeline
    without wearing the wave. The owner counts like anyone else.
    """
    seen, out = set(), []
    for item in items:
        repo = item.get("repository") or {}
        owner = repo.get("owner") or {}
        login = owner.get("login") or ""
        if (not login or repo.get("fork")
                or (repo.get("name") or "").lower() in OWN_REPOS):
            continue
        if login.lower() in seen:
            continue
        seen.add(login.lower())
        out.append({"login": login, "avatar": owner.get("avatar_url") or ""})
    return out


def users(token=""):
    """Everyone using the wave or the Action, or None without a token or if search failed."""
    if not token:
        return None
    items = []
    try:
        for q in SEARCHES:
            for page in (1, 2, 3):
                url = ("https://api.github.com/search/code?"
                       + urllib.parse.urlencode({"q": q, "per_page": 100, "page": page}))
                batch = _get(url, token).get("items") or []
                items.extend(batch)
                if len(batch) < 100:
                    break
    except Exception:
        return None
    people = users_from_items(items)
    seen = {u["login"].lower() for u in people}
    for login in KNOWN:
        if login.lower() not in seen and wears_wave(login, token):
            people.append({"login": login, "avatar": f"https://avatars.githubusercontent.com/{login}"})
    return people

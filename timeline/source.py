"""Fetch a GitHub contribution calendar and reduce it to weekly totals.

Two routes. With a token the GraphQL API gives exact daily counts. Without one
the public contributions fragment is parsed instead, which needs no credentials
and no scopes: handy for self-hosting, slightly coarser when GitHub serves
levels rather than counts.
"""

import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

API_URL = "https://api.github.com/graphql"
HTML_URL = "https://github.com/users/{login}/contributions"
USER_AGENT = "timeline"
TIMEOUT = 10

QUERY = (
    "query($login:String!,$from:DateTime!,$to:DateTime!){"
    "user(login:$login){contributionsCollection(from:$from,to:$to){"
    "contributionCalendar{weeks{contributionDays{contributionCount date}}}}}}"
)

# GitHub only exposes a 0-4 band when it omits exact counts. These midpoints keep
# the wave's shape honest even though the absolute numbers are approximate.
LEVEL_COUNTS = {0: 0, 1: 1, 2: 4, 3: 8, 4: 14}


class NotFound(Exception):
    """No such GitHub account."""


class Unavailable(Exception):
    """GitHub could not be reached, or refused the request."""


def _read(url, data=None, headers=None, timeout=TIMEOUT):
    base = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    base.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=base)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise NotFound(url) from exc
        raise Unavailable(f"HTTP {exc.code}") from exc
    except Exception as exc:                       # timeouts, DNS, TLS
        raise Unavailable(str(exc)) from exc


# ---------- route one: the GraphQL API, with a token ----------

def _weeks_from_api(login, token, days=371):
    to = datetime.now(timezone.utc).replace(microsecond=0)
    frm = to - timedelta(days=days)
    payload = json.dumps({"query": QUERY, "variables": {
        "login": login,
        "from": frm.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": to.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }}).encode()
    body = _read(API_URL, data=payload, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    data = json.loads(body)
    for err in data.get("errors") or []:
        if err.get("type") == "NOT_FOUND":
            raise NotFound(login)
    user = (data.get("data") or {}).get("user")
    if user is None:
        raise NotFound(login)
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in weeks]


# ---------- route two: the public fragment, no token ----------

_TD = re.compile(r"<td\b[^>]*ContributionCalendar-day[^>]*>")
_TOOLTIP = re.compile(r"<tool-tip\b[^>]*\bfor=\"([^\"]+)\"[^>]*>(.*?)</tool-tip>", re.S)
_COUNT_TEXT = re.compile(r"(\d[\d,]*)\s+contribution")


def _attr(tag, name):
    m = re.search(name + r"=\"([^\"]*)\"", tag)
    return m.group(1) if m else None


def _days_from_html(login):
    body = _read(HTML_URL.format(login=login), headers={
        "Accept": "text/html", "X-Requested-With": "XMLHttpRequest"})
    tooltips = {}
    for day_id, text in _TOOLTIP.findall(body):
        m = _COUNT_TEXT.search(text)
        tooltips[day_id] = int(m.group(1).replace(",", "")) if m else 0

    days = []
    for tag in _TD.findall(body):
        iso = _attr(tag, "data-date")
        if not iso:
            continue
        raw = _attr(tag, "data-count")
        if raw is not None and raw.isdigit():
            count = int(raw)
        elif _attr(tag, "id") in tooltips:
            count = tooltips[_attr(tag, "id")]
        else:
            level = _attr(tag, "data-level")
            count = LEVEL_COUNTS.get(int(level) if level and level.isdigit() else 0, 0)
        days.append((iso, count))
    if not days:
        raise NotFound(login)
    return days


def _group_into_weeks(days):
    """Sort by date and bucket into calendar weeks, dropping partial ones at either end.

    The current week is always incomplete, and counting it would print a dip into
    the water that is an artefact of the clock rather than of the work.
    """
    parsed = sorted({iso: count for iso, count in days}.items())
    if not parsed:
        return []
    start = date.fromisoformat(parsed[0][0])
    buckets = {}
    for iso, count in parsed:
        idx = (date.fromisoformat(iso) - start).days // 7
        buckets.setdefault(idx, []).append(count)
    keys = sorted(buckets)
    weeks = [buckets[k] for k in keys]
    if len(weeks) > 3:
        if len(weeks[0]) < 7:
            weeks = weeks[1:]
        if len(weeks[-1]) < 7:
            weeks = weeks[:-1]
    return [sum(w) for w in weeks]


# ---------- the façade ----------

def weekly_totals(login, token=None, weeks=52):
    """Return (totals, source) where source names the route that answered."""
    token = (token or "").strip()
    if token:
        try:
            api_weeks = _weeks_from_api(login, token)
            days = [d for w in api_weeks for d in w]
            totals = _group_into_weeks(days)
            if totals:
                return totals[-weeks:], "api"
        except NotFound:
            raise
        except Unavailable:
            pass                      # a token problem should not take the service down
    totals = _group_into_weeks(_days_from_html(login))
    return totals[-weeks:], "public"


# ---------- a small cache, useful while an instance stays warm ----------

_CACHE = {}
_CACHE_MAX = 512


def cached_weekly_totals(login, token=None, weeks=52, ttl=1800):
    key = (login.lower(), weeks, bool(token))
    now = time.time()
    hit = _CACHE.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = weekly_totals(login, token, weeks)
    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.clear()
    _CACHE[key] = (now, value)
    return value

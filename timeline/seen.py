"""People whose wave GitHub has loaded, kept in a Vercel Blob store.

Every image in a README reaches GitHub through its image proxy, camo, which sends
"github-camo" as its User-Agent. When camo asks for someone's wave, that person
has it on a GitHub page, so the render endpoint notes their login here. One blob
per login; its upload time is when camo last fetched it. Someone who removes the
wave drops off once camo has not asked for it in a while.

Uses Vercel Blob's HTTP API directly (the same calls @vercel/blob makes), with
the store's BLOB_READ_WRITE_TOKEN. Without a token every call is a no-op.
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime

API = os.environ.get("VERCEL_BLOB_API_URL") or "https://vercel.com/api/blob"
API_VERSION = "13"
PREFIX = "users/"
KEEP_DAYS = 30
LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


def token():
    return os.environ.get("BLOB_READ_WRITE_TOKEN") or ""


def _store_id(tok):
    # Read-write tokens look like vercel_blob_rw_<storeId>_<secret>.
    parts = tok.split("_")
    return parts[3] if len(parts) > 3 else ""


def _request(method, path, tok, body=None, headers=None, timeout=3):
    h = {"authorization": f"Bearer {tok}", "x-api-version": API_VERSION,
         "x-vercel-blob-store-id": _store_id(tok)}
    h.update(headers or {})
    req = urllib.request.Request(API + path, data=body, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def from_camo(user_agent):
    """True when the request is GitHub's image proxy loading a README image."""
    return "github-camo" in (user_agent or "").lower()


def record(login, tok=None):
    """Note that GitHub just loaded login's wave. Returns True if it was saved."""
    tok = token() if tok is None else tok
    if not tok or not login or not LOGIN.match(login):
        return False
    path = "/?" + urllib.parse.urlencode({"pathname": PREFIX + login})
    try:
        _request("PUT", path, tok, body=login.encode(), headers={
            "x-vercel-blob-access": "private", "x-add-random-suffix": "0",
            "x-allow-overwrite": "1", "x-content-type": "text/plain"})
        return True
    except Exception:
        return False


def _when(stamp):
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def logins_from_blobs(blobs, now=None, keep_days=KEEP_DAYS):
    """Logins seen within keep_days, newest first, one per person."""
    now = time.time() if now is None else now
    newest = {}
    for b in blobs:
        login = (b.get("pathname") or "")[len(PREFIX):]
        when = _when(b.get("uploadedAt") or "")
        if not LOGIN.match(login) or now - when > keep_days * 86400:
            continue
        key = login.lower()
        if key not in newest or when > newest[key][0]:
            newest[key] = (when, login)
    return [login for _, login in sorted(newest.values(), reverse=True)]


def recent(tok=None):
    """Logins GitHub has loaded a wave for lately, or None if the store can't be read."""
    tok = token() if tok is None else tok
    if not tok:
        return None
    blobs, cursor = [], None
    try:
        for _ in range(10):
            q = {"prefix": PREFIX, "limit": 1000}
            if cursor:
                q["cursor"] = cursor
            page = _request("GET", "?" + urllib.parse.urlencode(q), tok)
            blobs.extend(page.get("blobs") or [])
            cursor = page.get("cursor")
            if not page.get("hasMore") or not cursor:
                break
    except Exception:
        return None
    return logins_from_blobs(blobs)

# parser/date_filter.py
import os
import re
from datetime import datetime, timedelta, timezone

from dateutil import parser as dateparser

MAX_AGE_DAYS = int(os.getenv("MAX_ARTICLE_AGE_DAYS", "180"))

# Matches /YYYY/MM/ or /YYYY/MM/DD/ embedded in article URLs
# (Krebs, TheHackerNews, and most date-pathed blogs).
_URL_DATE = re.compile(r"/(20\d{2})/(\d{1,2})(?:/(\d{1,2}))?/")


def _date_from_url(url: str):
    """Derive a publish date from a date-pathed URL, or None if absent."""
    if not url:
        return None
    m = _URL_DATE.search(url)
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    day = int(m.group(3)) if m.group(3) else 1
    if not (1 <= month <= 12):
        return None
    try:
        # clamp day to 28 so we never raise on month-length edge cases
        return datetime(year, month, min(max(day, 1), 28), tzinfo=timezone.utc)
    except Exception:
        return None


def _date_from_text(date_str: str):
    """Parse a free-text date string, or None if unreadable."""
    if not date_str or not str(date_str).strip():
        return None
    try:
        dt = dateparser.parse(str(date_str), fuzzy=True)
    except Exception:
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_recent(date_str: str, url: str = "") -> bool:
    """
    True if the article is within the age window.

    Resolution order:
      1. the page's own date string (most precise when present)
      2. the date embedded in the URL path (reliable for archived pages
         where the page date didn't extract)
      3. fail-open: if NEITHER source yields a date, keep the article
         (a missing date must never silently drop a useful article).
    """
    dt = _date_from_text(date_str) or _date_from_url(url)
    if dt is None:
        return True  # fail-open

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    keep = dt >= cutoff
    if not keep:
        print(f"[DEBUG] DROP old: {dt.date()} {url[:60]}")
    return keep
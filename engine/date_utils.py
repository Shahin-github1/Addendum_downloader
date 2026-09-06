import os
import sys
import datetime
import re
from typing import Any, Optional

def get_app_root() -> str:
    """Returns the base application directory for both source and PyInstaller frozen EXE."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_ordinal_suffix(day: int) -> str:
    if 11 <= (day % 100) <= 13:
        return f"{day}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"

def get_day_folder_name(target_date: datetime.date = None) -> str:
    """Returns folder name in the format: '10th September 2026'."""
    if target_date is None:
        target_date = datetime.date.today()
    day_with_suffix = get_ordinal_suffix(target_date.day)
    month_name = target_date.strftime("%B")
    return f"{day_with_suffix} {month_name} {target_date.year}"

def get_indian_financial_year(target_date: datetime.date = None) -> dict:
    """
    Computes Indian Financial Year (April 1 to March 31).
    Returns dict with different common representations.
    """
    if target_date is None:
        target_date = datetime.date.today()
    
    if target_date.month >= 4:
        start_year = target_date.year
        end_year = target_date.year + 1
    else:
        start_year = target_date.year - 1
        end_year = target_date.year
    
    short_end = str(end_year)[-2:]
    return {
        "start_year": str(start_year),
        "end_year": str(end_year),
        "short": f"{start_year}-{short_end}",         # e.g., "2026-27"
        "short_slash": f"{start_year}/{short_end}",   # e.g., "2026/27"
        "long": f"{start_year}-{end_year}",           # e.g., "2026-2027"
        "long_slash": f"{start_year}/{end_year}",     # e.g., "2026/2027"
        "fy_label": f"FY {start_year}-{short_end}"    # e.g., "FY 2026-27"
    }

def clean_filename(filename: str) -> str:
    """Sanitizes strings for Windows filesystem safety."""
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', filename)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:180]  # Avoid MAX_PATH issues

def parse_flexible_date(date_str: str) -> datetime.date:
    """
    Parses diverse Indian AMC date formats into a datetime.date object.
    Supports DD-MM-YYYY, YYYY-MM-DD, DD-Mon-YYYY, DD Month YYYY, etc.
    Returns None if unparseable.
    """
    if not date_str:
        return None
    s = str(date_str).strip()
    # Normalize slashes and dots to hyphens
    s = re.sub(r'[./]', '-', s)
    s = re.sub(r'\s+', ' ', s)

    # List of strptime candidate patterns
    candidate_patterns = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%B %d %Y",
        "%d-%m-%y",
        "%m-%d-%Y"
    ]

    for pat in candidate_patterns:
        try:
            return datetime.datetime.strptime(s, pat).date()
        except Exception:
            pass

    # Try extracting date pattern via regex if embedded in surrounding text
    patterns = [
        r'\b(\d{1,2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*-(\d{2,4})\b',
        r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b',
        r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b',
    ]
    for p in patterns:
        m = re.search(p, s, re.I)
        if m:
            matched_substr = m.group(0)
            for pat in candidate_patterns:
                try:
                    return datetime.datetime.strptime(matched_substr, pat).date()
                except Exception:
                    pass

    return None

def is_date_on_or_after(date_val: Any, cutoff_date: datetime.date) -> bool:
    """
    Checks if a given date string or datetime.date is on or after cutoff_date.
    If date_val cannot be parsed, returns True by default so valid files are not lost.
    """
    if not cutoff_date:
        return True
    if isinstance(date_val, datetime.date):
        return date_val >= cutoff_date
    parsed = parse_flexible_date(str(date_val))
    if parsed is None:
        return True  # Lenient fallback if date not determinable
    return parsed >= cutoff_date


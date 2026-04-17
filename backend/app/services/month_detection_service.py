from __future__ import annotations

import re
from typing import Optional


MONTH_MAP = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def detect_month_from_filename(filename: str) -> Optional[str]:
    text = filename.lower().strip()

    # Example: LC Data End Jan 2026.xlsx
    match = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})", text)
    if match:
        month = MONTH_MAP[match.group(1)]
        year = match.group(2)
        return f"{year}-{month}"

    # Example: 2026-01 or 2026_01 or 2026/01
    match = re.search(r"(\d{4})[-_/](\d{1,2})", text)
    if match:
        year = match.group(1)
        month = int(match.group(2))
        if 1 <= month <= 12:
            return f"{year}-{month:02d}"

    return None
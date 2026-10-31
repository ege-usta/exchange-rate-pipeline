"""Step 1 - Extract: download the daily exchange-rate files from the Central Bank of Türkiye (TCMB)."""

import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE_URL = "https://www.tcmb.gov.tr/kurlar"


def url_for(day: date) -> str:
    # Example: https://www.tcmb.gov.tr/kurlar/202610/30102026.xml
    return f"{BASE_URL}/{day:%Y%m}/{day:%d%m%Y}.xml"


def workdays(start: date, end: date):
    """Every Monday-Friday between start and end. TCMB publishes nothing at weekends."""
    day = start
    while day <= end:
        if day.weekday() < 5:
            yield day
        day += timedelta(days=1)


def download_day(day: date, raw_dir: Path) -> Path | None:
    """Save one day's XML into raw_dir. Returns None on holidays (TCMB answers 404)."""
    target = raw_dir / f"{day:%Y-%m-%d}.xml"
    if target.exists():  # already downloaded before, don't ask the server again
        return target
    try:
        with urllib.request.urlopen(url_for(day), timeout=20) as response:
            target.write_bytes(response.read())
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    time.sleep(0.3)  # be polite to the server
    return target


def extract(start: date, end: date, raw_dir: Path) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for day in workdays(start, end):
        path = download_day(day, raw_dir)
        if path:
            files.append(path)
    return files

"""Run the whole pipeline: extract -> transform -> load -> report.

Example:
    python run.py --start 2026-01-01 --end 2026-10-30
"""

import argparse
from datetime import date
from pathlib import Path

from pipeline.extract import extract
from pipeline.load import connect, load
from pipeline.report import build_report
from pipeline.transform import parse_rates

DATA = Path("data")


def main() -> None:
    parser = argparse.ArgumentParser(description="TCMB exchange rate pipeline")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()

    files = extract(args.start, args.end, DATA / "raw")
    print(f"1. extract:   {len(files)} daily files")

    rows = []
    for path in files:
        rows += parse_rates(path.read_text(encoding="utf-8"))
    print(f"2. transform: {len(rows)} rows")

    connection = connect(DATA / "rates.db")
    print(f"3. load:      {load(connection, rows)} rows saved to {DATA / 'rates.db'}")

    report = build_report(connection, Path("reports"))
    print(f"4. report:    {report}")


if __name__ == "__main__":
    main()

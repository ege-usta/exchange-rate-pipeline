"""Step 4 - Report: answer simple questions with SQL and draw a chart."""

import sqlite3
from pathlib import Path

MONTHLY_AVERAGE = """
SELECT substr(date, 1, 7) AS month, code, ROUND(AVG(buying), 4) AS average
FROM rates
WHERE code IN ('USD', 'EUR')
GROUP BY month, code
ORDER BY month, code;
"""

# LAG() looks at the previous working day's rate for the same currency.
BIGGEST_DAILY_MOVES = """
WITH daily AS (
    SELECT date, code, buying,
           LAG(buying) OVER (PARTITION BY code ORDER BY date) AS previous
    FROM rates
    WHERE code IN ('USD', 'EUR')
)
SELECT date, code, ROUND(100.0 * (buying - previous) / previous, 2) AS change_pct
FROM daily
WHERE previous IS NOT NULL
ORDER BY ABS(change_pct) DESC
LIMIT 5;
"""

SUMMARY = """
SELECT COUNT(DISTINCT date), COUNT(DISTINCT code), MIN(date), MAX(date) FROM rates;
"""


def build_report(connection: sqlite3.Connection, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    days, currencies, first, last = connection.execute(SUMMARY).fetchone()

    lines = [
        "# Exchange rate report",
        "",
        f"{days} working days, {currencies} currencies, from {first} to {last}.",
        "Source: Central Bank of the Republic of Türkiye (TCMB), forex buying rate.",
        "",
        "## Monthly average (TRY)",
        "",
        "| Month | USD | EUR |",
        "|---|---|---|",
    ]
    by_month: dict[str, dict[str, float]] = {}
    for month, code, average in connection.execute(MONTHLY_AVERAGE):
        by_month.setdefault(month, {})[code] = average
    for month, values in by_month.items():
        lines.append(f"| {month} | {values.get('USD', '-')} | {values.get('EUR', '-')} |")

    lines += ["", "## Biggest one-day moves", "", "| Date | Currency | Change |", "|---|---|---|"]
    for day, code, change in connection.execute(BIGGEST_DAILY_MOVES):
        lines.append(f"| {day} | {code} | {change:+.2f}% |")

    report = out_dir / "report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    draw_chart(connection, out_dir / "usd_eur.png")
    return report


def draw_chart(connection: sqlite3.Connection, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")  # draw to a file, no window
    import matplotlib.pyplot as plt
    from datetime import date

    fig, ax = plt.subplots(figsize=(9, 4))
    for code in ("USD", "EUR"):
        rows = connection.execute(
            "SELECT date, buying FROM rates WHERE code = ? ORDER BY date", (code,)
        ).fetchall()
        ax.plot([date.fromisoformat(d) for d, _ in rows], [b for _, b in rows], label=code)
    ax.set_title("USD and EUR against the Turkish lira (TCMB)")
    ax.set_ylabel("TRY")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)

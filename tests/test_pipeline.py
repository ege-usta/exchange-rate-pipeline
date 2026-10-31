from datetime import date
from pathlib import Path

from pipeline.extract import url_for, workdays
from pipeline.load import connect, load
from pipeline.report import build_report
from pipeline.transform import parse_rates, to_number

SAMPLE = (Path(__file__).parent / "fixtures" / "30102026.xml").read_text(encoding="utf-8")


def test_url_for_builds_tcmb_address():
    assert url_for(date(2026, 10, 30)) == "https://www.tcmb.gov.tr/kurlar/202610/30102026.xml"


def test_workdays_skips_weekends():
    days = list(workdays(date(2026, 10, 30), date(2026, 11, 2)))  # Fri .. Mon
    assert days == [date(2026, 10, 30), date(2026, 11, 2)]


def test_to_number_handles_empty_tags():
    assert to_number("49.7747") == 49.7747
    assert to_number(None) is None
    assert to_number("   ") is None


def test_parse_rates_reads_usd():
    rows = {row["code"]: row for row in parse_rates(SAMPLE)}
    assert rows["USD"]["date"] == "2026-10-30"
    assert rows["USD"]["buying"] == 49.7747


def test_parse_rates_converts_yen_to_one_unit():
    rows = {row["code"]: row for row in parse_rates(SAMPLE)}
    assert rows["JPY"]["buying"] == 0.315605  # TCMB gives the rate for 100 yen


def test_parse_rates_keeps_currency_without_selling_rate():
    rows = {row["code"]: row for row in parse_rates(SAMPLE)}
    assert rows["XDR"]["selling"] is None
    assert rows["XDR"]["name"] == "SPECIAL DRAWING RIGHT (SDR)"  # extra spaces removed


def test_load_twice_does_not_duplicate(tmp_path):
    connection = connect(tmp_path / "test.db")
    rows = parse_rates(SAMPLE)
    load(connection, rows)
    load(connection, rows)
    (count,) = connection.execute("SELECT COUNT(*) FROM rates").fetchone()
    assert count == len(rows)


def test_report_is_written(tmp_path):
    connection = connect(tmp_path / "test.db")
    load(connection, parse_rates(SAMPLE))
    report = build_report(connection, tmp_path / "reports")
    assert "| 2026-10 | 49.7747 |" in report.read_text(encoding="utf-8")
    assert (tmp_path / "reports" / "usd_eur.png").exists()

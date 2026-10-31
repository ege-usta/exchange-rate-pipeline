"""Step 2 - Transform: turn one TCMB XML file into clean rows."""

import xml.etree.ElementTree as ET
from datetime import datetime


def to_number(text: str | None) -> float | None:
    """'49.7747' -> 49.7747, and an empty tag -> None."""
    if text is None or not text.strip():
        return None
    return float(text)


def parse_rates(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    day = datetime.strptime(root.attrib["Date"], "%m/%d/%Y").date().isoformat()

    rows = []
    for currency in root.findall("Currency"):
        unit = int(currency.findtext("Unit"))
        buying = to_number(currency.findtext("ForexBuying"))
        selling = to_number(currency.findtext("ForexSelling"))
        if buying is None:
            continue  # no usable rate for this currency today
        rows.append(
            {
                "date": day,
                "code": currency.attrib["Kod"],
                "name": currency.findtext("CurrencyName").strip(),
                # Some rates are given for 100 units (e.g. JPY). Convert everything to 1 unit.
                "buying": round(buying / unit, 6),
                "selling": round(selling / unit, 6) if selling is not None else None,
            }
        )
    return rows

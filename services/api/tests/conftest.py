from __future__ import annotations

import csv
import io

import pytest

from app.storage.analysis_store import clear_last_analysis


@pytest.fixture(autouse=True)
def reset_analysis_store() -> None:
    clear_last_analysis()


def _to_csv_bytes(rows: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "incident_id",
            "date",
            "country",
            "customer_type",
            "tracking_number",
            "carrier",
            "category",
            "description",
            "status",
            "customer_email",
            "satisfaction_score",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


@pytest.fixture
def trackflow_expected_csv_bytes() -> bytes:
    rows: list[dict[str, object]] = []

    categories: list[str] = (
        ["LOST_PARCEL"] * 14
        + ["DELAYED_DELIVERY"] * 38
        + ["WRONG_ADDRESS"] * 19
        + ["RETURN_REQUEST"] * 17
        + ["DAMAGE"] * 7
    )
    statuses: list[str] = (["CLOSED"] * 52) + (["OPEN"] * 29) + (["DISCARDED"] * 14)
    countries: list[str] = (["US"] * 50) + (["ES"] * 45)
    closed_scores: list[int] = [1] * 6 + [2] * 11 + [3] * 15 + [4] * 14 + [5] * 6

    score_index = 0
    for idx in range(95):
        status = statuses[idx]
        country = countries[idx]
        carrier = "UPS" if country == "US" else "MRW"

        if status == "CLOSED":
            satisfaction_score: int | str = closed_scores[score_index]
            score_index += 1
        else:
            satisfaction_score = ""

        rows.append(
            {
                "incident_id": f"TRF-{idx + 1:06d}",
                "date": f"2026-08-{(idx % 28) + 1:02d}",
                "country": country,
                "customer_type": "B2B" if idx % 2 == 0 else "B2C",
                "tracking_number": f"TRK{idx + 1:08d}",
                "carrier": carrier,
                "category": categories[idx],
                "description": f"Valid incident description {idx + 1}",
                "status": status,
                "customer_email": f"customer{idx + 1}@example.com",
                "satisfaction_score": satisfaction_score,
            }
        )

    rows.append(
        {
            "incident_id": "TRF-000096",
            "date": "2026-08-10",
            "country": "US",
            "customer_type": "B2C",
            "tracking_number": "1234",
            "carrier": "UPS",
            "category": "LOST_PARCEL",
            "description": "Tracking invalid",
            "status": "OPEN",
            "customer_email": "invalid1@example.com",
            "satisfaction_score": "",
        }
    )
    rows.append(
        {
            "incident_id": "TRF-000097",
            "date": "2026-08-11",
            "country": "US",
            "customer_type": "B2C",
            "tracking_number": "TRK00000097",
            "carrier": "MRW",
            "category": "DAMAGE",
            "description": "Carrier mismatch",
            "status": "OPEN",
            "customer_email": "invalid2@example.com",
            "satisfaction_score": "",
        }
    )
    rows.append(
        {
            "incident_id": "TRF-000098",
            "date": "2026-08-12",
            "country": "ES",
            "customer_type": "B2B",
            "tracking_number": "TRK00000098",
            "carrier": "SEUR",
            "category": "UNKNOWN",
            "description": "Unknown category",
            "status": "DISCARDED",
            "customer_email": "invalid3@example.com",
            "satisfaction_score": "",
        }
    )
    rows.append(
        {
            "incident_id": "TRF-000099",
            "date": "2026-08-13",
            "country": "ES",
            "customer_type": "B2C",
            "tracking_number": "TRK00000099",
            "carrier": "MRW",
            "category": "RETURN_REQUEST",
            "description": "Bad email",
            "status": "OPEN",
            "customer_email": "invalid4.example.com",
            "satisfaction_score": "",
        }
    )
    rows.append(
        {
            "incident_id": "TRF-000100",
            "date": "2026-08-14",
            "country": "US",
            "customer_type": "B2B",
            "tracking_number": "TRK00000100",
            "carrier": "FEDEX",
            "category": "DELAYED_DELIVERY",
            "description": "Closed without score",
            "status": "CLOSED",
            "customer_email": "invalid5@example.com",
            "satisfaction_score": "",
        }
    )

    return _to_csv_bytes(rows)


@pytest.fixture
def single_valid_csv_bytes() -> bytes:
    return _to_csv_bytes(
        [
            {
                "incident_id": "TRF-123456",
                "date": "2026-08-01",
                "country": "US",
                "customer_type": "B2C",
                "tracking_number": "TRK12345678",
                "carrier": "UPS",
                "category": "DAMAGE",
                "description": "Valid issue",
                "status": "CLOSED",
                "customer_email": "user@example.com",
                "satisfaction_score": 5,
            }
        ]
    )

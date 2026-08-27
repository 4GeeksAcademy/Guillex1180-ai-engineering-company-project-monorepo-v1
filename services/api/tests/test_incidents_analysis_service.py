from __future__ import annotations

import pytest

from app.services.incidents_analysis_service import (
    AnalysisServiceError,
    analyze_incidents_bytes,
    export_analysis_csv,
)


def test_valid_csv_analysis(single_valid_csv_bytes: bytes) -> None:
    result = analyze_incidents_bytes(single_valid_csv_bytes)

    assert result["total_processed"] == 1
    assert result["valid_records"] == 1
    assert result["invalid_records"] == 0
    assert result["valid_records"] + result["invalid_records"] == result["total_processed"]


def test_context_expected_metrics(trackflow_expected_csv_bytes: bytes) -> None:
    result = analyze_incidents_bytes(trackflow_expected_csv_bytes)

    assert result["total_processed"] == 100
    assert result["valid_records"] == 95
    assert result["invalid_records"] == 5
    assert result["validation_errors_raw"]["invalid_tracking_number"] == 1
    assert result["validation_errors_raw"]["carrier_country_mismatch"] == 1
    assert result["validation_errors_raw"]["invalid_or_missing_category"] == 1
    assert result["validation_errors_raw"]["invalid_or_missing_email"] == 1
    assert result["validation_errors_raw"]["closed_no_score"] == 1

    assert result["by_category"] == {
        "DELAYED_DELIVERY": 38,
        "WRONG_ADDRESS": 19,
        "RETURN_REQUEST": 17,
        "LOST_PARCEL": 14,
        "DAMAGE": 7,
    }
    assert result["by_status"] == {"OPEN": 29, "CLOSED": 52, "DISCARDED": 14}
    assert result["average_satisfaction"] == 3.06


def test_missing_required_field(single_valid_csv_bytes: bytes) -> None:
    data = single_valid_csv_bytes.decode("utf-8").replace("TRK12345678", "")
    result = analyze_incidents_bytes(data.encode("utf-8"))

    assert result["invalid_records"] == 1
    assert result["validation_errors_raw"]["invalid_tracking_number"] == 1


def test_out_of_range_satisfaction(single_valid_csv_bytes: bytes) -> None:
    data = single_valid_csv_bytes.decode("utf-8").replace(",5\r\n", ",7\r\n")
    result = analyze_incidents_bytes(data.encode("utf-8"))

    assert result["invalid_records"] == 1
    assert result["validation_errors_raw"]["invalid_satisfaction_score"] == 1


def test_invalid_status(single_valid_csv_bytes: bytes) -> None:
    data = single_valid_csv_bytes.decode("utf-8").replace("CLOSED", "PENDING")
    result = analyze_incidents_bytes(data.encode("utf-8"))

    assert result["invalid_records"] == 1
    assert result["validation_errors_raw"]["invalid_status"] == 1


def test_average_satisfaction_only_closed_and_scored(trackflow_expected_csv_bytes: bytes) -> None:
    result = analyze_incidents_bytes(trackflow_expected_csv_bytes)
    assert result["average_satisfaction"] == 3.06


def test_empty_csv_error() -> None:
    with pytest.raises(AnalysisServiceError, match="vacío"):
        analyze_incidents_bytes(b"")


def test_non_csv_error() -> None:
    with pytest.raises(AnalysisServiceError, match="CSV válido"):
        analyze_incidents_bytes(b"\x00\x01\x02\x03")


def test_missing_columns_error() -> None:
    with pytest.raises(AnalysisServiceError, match="Faltan columnas obligatorias"):
        analyze_incidents_bytes(b"a,b\n1,2\n")


def test_export_rows_structure(single_valid_csv_bytes: bytes) -> None:
    result = analyze_incidents_bytes(single_valid_csv_bytes)
    exported = export_analysis_csv(result)
    assert "metric,value" in exported
    assert "total_processed,1" in exported
    assert "status_closed,1" in exported

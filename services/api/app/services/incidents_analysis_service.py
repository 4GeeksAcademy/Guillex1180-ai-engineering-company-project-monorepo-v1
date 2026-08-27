from __future__ import annotations

import csv
import io
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

TRACKFLOW_REQUIRED_COLUMNS = [
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
]
TRACKFLOW_COUNTRIES = {"US", "ES"}
TRACKFLOW_CUSTOMER_TYPES = {"B2B", "B2C"}
TRACKFLOW_CATEGORIES = {
    "LOST_PARCEL",
    "DELAYED_DELIVERY",
    "WRONG_ADDRESS",
    "RETURN_REQUEST",
    "DAMAGE",
}
TRACKFLOW_CARRIERS_BY_COUNTRY = {
    "US": {"UPS", "FEDEX", "DHL_US"},
    "ES": {"MRW", "SEUR", "DHL_ES", "LOCAL_ES"},
}
TRACKFLOW_STATUS_VALUES = {"OPEN", "CLOSED", "DISCARDED"}
SATISFACTION_RANGE = (1, 5)

STATUS_LABELS_ES = {
    "OPEN": "Abierto",
    "CLOSED": "Cerrado",
    "DISCARDED": "Descartado",
}

REASON_LABELS_ES = {
    "invalid_tracking_number": "Tracking inválido",
    "carrier_country_mismatch": "Carrier/país inconsistente",
    "invalid_or_missing_category": "Categoría faltante/inválida",
    "invalid_or_missing_email": "Email faltante/inválido",
    "closed_no_score": "Cerrado sin satisfacción",
    "invalid_country": "País inválido",
    "invalid_customer_type": "Tipo de cliente inválido",
    "invalid_status": "Estado inválido",
    "invalid_date": "Fecha inválida",
    "invalid_description": "Descripción inválida",
    "invalid_incident_id": "ID de incidente inválido",
    "duplicate_record": "Registro duplicado",
    "invalid_satisfaction_score": "Satisfacción inválida",
}


class AnalysisServiceError(Exception):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_upper(value: Any) -> str:
    return _normalize_text(value).upper()


def _find_repo_root(start_path: Path) -> Path:
    current = start_path.resolve()
    for parent in [current] + list(current.parents):
        if (parent / "CONTEXT-trackflow.es.md").exists():
            return parent
    return start_path.resolve()


def context_trackflow_path() -> Path:
    repo_root = _find_repo_root(Path(__file__).parent)
    return repo_root / "CONTEXT-trackflow.es.md"


def parse_context_expected_results(context_path: Path) -> dict[str, Any] | None:
    if not context_path.exists():
        return None

    text = context_path.read_text(encoding="utf-8")

    def extract_single_int(pattern: str) -> int | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return int(match.group(1)) if match else None

    def extract_single_float(pattern: str) -> float | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return float(match.group(1)) if match else None

    total_records = extract_single_int(r"Total de filas:\*\*\s*(\d+)")
    valid_records = extract_single_int(r"Registros válidos:\s*(\d+)\*\*")
    invalid_records = extract_single_int(r"Registros inválidos:\s*(\d+)\*\*")
    expected_mean = extract_single_float(r"Promedio:\s*\*\*(\d+(?:\.\d+)?)\*\*")

    category_counts: dict[str, int] = {}
    category_pattern = r"\|\s*`(LOST_PARCEL|DELAYED_DELIVERY|WRONG_ADDRESS|RETURN_REQUEST|DAMAGE)`\s*\|\s*(\d+)\s*\|"
    for key, value in re.findall(category_pattern, text):
        category_counts[key] = int(value)

    status_counts: dict[str, int] = {}
    status_pattern = r"\|\s*`(OPEN|CLOSED|DISCARDED)`\s*\|\s*(\d+)\s*\|"
    for key, value in re.findall(status_pattern, text):
        status_counts[key] = int(value)

    invalid_breakdown: dict[str, int] = {}
    invalid_patterns = {
        "invalid_tracking_number": r"tracking_number`\s+faltante\s+o\s+inválido\s*\|\s*(\d+)\s*\|",
        "carrier_country_mismatch": r"Carrier\s+inválido\s+para\s+el\s+país\s+declarado\s*\|\s*(\d+)\s*\|",
        "invalid_or_missing_category": r"category`\s+faltante\s+o\s+inválida\s*\|\s*(\d+)\s*\|",
        "invalid_or_missing_email": r"customer_email`\s+faltante\s+o\s+inválido\s*\|\s*(\d+)\s*\|",
        "closed_no_score": r"status\s*=\s*CLOSED`\s+sin\s+`satisfaction_score`\s*\|\s*(\d+)\s*\|",
    }
    for key, pattern in invalid_patterns.items():
        count = extract_single_int(pattern)
        if count is not None:
            invalid_breakdown[key] = count

    if total_records is None or valid_records is None or invalid_records is None:
        return None

    return {
        "total_records": total_records,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "invalid_breakdown": invalid_breakdown,
        "category_counts": category_counts,
        "status_counts": status_counts,
        "closed_satisfaction_mean": expected_mean,
    }


def load_incidents_csv_from_path(csv_path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(csv_path)
    except Exception as error:
        raise AnalysisServiceError(f"Error al leer el CSV '{csv_path}': {error}") from error


def load_incidents_csv_from_bytes(content: bytes) -> pd.DataFrame:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise AnalysisServiceError("El archivo no tiene un formato CSV válido.") from error

    if "\x00" in text:
        raise AnalysisServiceError("El archivo no tiene un formato CSV válido.")

    try:
        df = pd.read_csv(io.StringIO(text))
    except Exception as error:
        raise AnalysisServiceError("El archivo no tiene un formato CSV válido.") from error

    if len(df.columns) == 1 and str(df.columns[0]).startswith("Unnamed"):
        raise AnalysisServiceError("El archivo no tiene un formato CSV válido.")

    return df


def ensure_required_columns(df: pd.DataFrame) -> None:
    missing = [column for column in TRACKFLOW_REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise AnalysisServiceError(f"Faltan columnas obligatorias: {', '.join(missing)}.")


def _add_error(errors: list[dict[str, Any]], row_number: int, reason_key: str, message: str) -> None:
    errors.append(
        {
            "row": row_number,
            "reason_key": reason_key,
            "message": message,
        }
    )


def validate_incidents(df: pd.DataFrame) -> dict[str, Any]:
    ensure_required_columns(df)
    errors: list[dict[str, Any]] = []

    duplicated_series = df.duplicated(subset=["incident_id"], keep=False)

    for index, row in df.iterrows():
        row_number = int(index) + 2

        incident_id = _normalize_text(row.get("incident_id"))
        if not re.fullmatch(r"TRF-\d{6}", incident_id):
            _add_error(errors, row_number, "invalid_incident_id", f"Fila {row_number}: incident_id inválido")

        date_value = _normalize_text(row.get("date"))
        try:
            datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError:
            _add_error(errors, row_number, "invalid_date", f"Fila {row_number}: fecha inválida en 'date'")

        country = _normalize_upper(row.get("country"))
        if country not in TRACKFLOW_COUNTRIES:
            _add_error(errors, row_number, "invalid_country", f"Fila {row_number}: país inválido")

        customer_type = _normalize_upper(row.get("customer_type"))
        if customer_type not in TRACKFLOW_CUSTOMER_TYPES:
            _add_error(errors, row_number, "invalid_customer_type", f"Fila {row_number}: customer_type inválido")

        tracking_number = _normalize_text(row.get("tracking_number"))
        if len(tracking_number) < 8:
            _add_error(errors, row_number, "invalid_tracking_number", f"Fila {row_number}: tracking_number faltante o inválido")

        category = _normalize_upper(row.get("category"))
        if category not in TRACKFLOW_CATEGORIES:
            _add_error(errors, row_number, "invalid_or_missing_category", f"Fila {row_number}: category faltante o inválida")

        description = _normalize_text(row.get("description"))
        if len(description) < 5:
            _add_error(errors, row_number, "invalid_description", f"Fila {row_number}: description vacía o demasiado corta")

        status = _normalize_upper(row.get("status"))
        if status not in TRACKFLOW_STATUS_VALUES:
            _add_error(errors, row_number, "invalid_status", f"Fila {row_number}: status no permitido")

        email = _normalize_text(row.get("customer_email"))
        if "@" not in email:
            _add_error(errors, row_number, "invalid_or_missing_email", f"Fila {row_number}: customer_email faltante o inválido")

        carrier = _normalize_upper(row.get("carrier"))
        allowed_carriers = TRACKFLOW_CARRIERS_BY_COUNTRY.get(country, set())
        if carrier not in allowed_carriers:
            _add_error(errors, row_number, "carrier_country_mismatch", f"Fila {row_number}: carrier inválido para el país declarado")

        satisfaction_raw = row.get("satisfaction_score")
        satisfaction_text = _normalize_text(satisfaction_raw)

        if status == "CLOSED" and satisfaction_text == "":
            _add_error(errors, row_number, "closed_no_score", f"Fila {row_number}: status CLOSED sin satisfaction_score")
        elif satisfaction_text != "":
            parsed = pd.to_numeric(pd.Series([satisfaction_raw]), errors="coerce").iloc[0]
            if pd.isna(parsed) or float(parsed).is_integer() is False:
                _add_error(errors, row_number, "invalid_satisfaction_score", f"Fila {row_number}: satisfaction_score inválido")
            else:
                value = int(parsed)
                if value < SATISFACTION_RANGE[0] or value > SATISFACTION_RANGE[1]:
                    _add_error(errors, row_number, "invalid_satisfaction_score", f"Fila {row_number}: satisfaction_score fuera de rango")

        if bool(duplicated_series.loc[index]):
            _add_error(errors, row_number, "duplicate_record", f"Fila {row_number}: incident_id duplicado")

    invalid_rows = sorted({error["row"] for error in errors})
    invalid_indices = [row - 2 for row in invalid_rows]

    invalid_records = df.iloc[invalid_indices].copy() if invalid_indices else df.iloc[0:0].copy()
    valid_records = df.drop(index=invalid_indices).copy() if invalid_indices else df.copy()

    reason_counts = Counter(error["reason_key"] for error in errors)
    invalid_by_reason = {
        REASON_LABELS_ES.get(reason, reason): count
        for reason, count in sorted(reason_counts.items())
    }

    return {
        "errors": errors,
        "reason_counts": dict(reason_counts),
        "invalid_by_reason": invalid_by_reason,
        "valid_records": valid_records,
        "invalid_records": invalid_records,
    }


def calculate_incident_metrics(valid_records: pd.DataFrame, invalid_records: pd.DataFrame) -> dict[str, Any]:
    total_processed = len(valid_records) + len(invalid_records)

    by_category: dict[str, int] = {}
    if not valid_records.empty:
        by_category = (
            valid_records["category"]
            .astype(str)
            .str.strip()
            .str.upper()
            .value_counts()
            .to_dict()
        )

    by_status = {"OPEN": 0, "CLOSED": 0, "DISCARDED": 0}
    if not valid_records.empty:
        status_counts = (
            valid_records["status"]
            .astype(str)
            .str.strip()
            .str.upper()
            .value_counts()
            .to_dict()
        )
        for key in by_status:
            by_status[key] = int(status_counts.get(key, 0))

    average_satisfaction: float | None = None
    if not valid_records.empty:
        closed = valid_records[
            valid_records["status"].astype(str).str.strip().str.upper() == "CLOSED"
        ]
        if not closed.empty:
            scores = pd.to_numeric(closed["satisfaction_score"], errors="coerce").dropna()
            scores = scores[(scores >= SATISFACTION_RANGE[0]) & (scores <= SATISFACTION_RANGE[1])]
            if not scores.empty:
                average_satisfaction = round(float(scores.mean()), 2)

    return {
        "total_processed": int(total_processed),
        "valid_records": int(len(valid_records)),
        "invalid_records": int(len(invalid_records)),
        "by_category": {k: int(v) for k, v in by_category.items()},
        "by_status": {k: int(v) for k, v in by_status.items()},
        "average_satisfaction": average_satisfaction,
    }


def analyze_incidents(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        raise AnalysisServiceError("El archivo CSV está vacío.")

    validation = validate_incidents(df)
    metrics = calculate_incident_metrics(
        valid_records=validation["valid_records"],
        invalid_records=validation["invalid_records"],
    )

    result = {
        **metrics,
        "validation_errors": validation["invalid_by_reason"],
        "validation_errors_raw": validation["reason_counts"],
        "validation_error_details": [error["message"] for error in validation["errors"]],
    }

    return result


def analyze_incidents_path(csv_path: Path) -> dict[str, Any]:
    df = load_incidents_csv_from_path(csv_path)
    return analyze_incidents(df)


def analyze_incidents_bytes(content: bytes) -> dict[str, Any]:
    if not content:
        raise AnalysisServiceError("El archivo CSV está vacío.")
    df = load_incidents_csv_from_bytes(content)
    return analyze_incidents(df)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.strip().lower())


def flatten_results_for_export(result: dict[str, Any]) -> list[tuple[str, str | int | float]]:
    rows: list[tuple[str, str | int | float]] = [
        ("total_processed", result["total_processed"]),
        ("valid_records", result["valid_records"]),
        ("invalid_records", result["invalid_records"]),
    ]

    for category, value in result["by_category"].items():
        rows.append((f"category_{_slugify(category)}", value))

    for status_key in ["OPEN", "CLOSED", "DISCARDED"]:
        rows.append((f"status_{status_key.lower()}", result["by_status"].get(status_key, 0)))

    if result["average_satisfaction"] is None:
        rows.append(("average_satisfaction_closed", ""))
    else:
        rows.append(("average_satisfaction_closed", result["average_satisfaction"]))

    return rows


def export_analysis_csv(result: dict[str, Any], header: tuple[str, str] = ("metric", "value")) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([header[0], header[1]])
    writer.writerows(flatten_results_for_export(result))
    return output.getvalue()


def verify_against_context(result: dict[str, Any], context_path: Path | None = None) -> list[str]:
    context_file = context_path or context_trackflow_path()
    expected = parse_context_expected_results(context_file)
    if expected is None:
        return ["Verificación CONTEXT-trackflow no disponible: no se pudo leer el bloque esperado."]

    mismatches: list[str] = []

    if result["total_processed"] != expected["total_records"]:
        mismatches.append(f"Total registros esperado {expected['total_records']}, obtenido {result['total_processed']}.")
    if result["valid_records"] != expected["valid_records"]:
        mismatches.append(f"Registros válidos esperado {expected['valid_records']}, obtenido {result['valid_records']}.")
    if result["invalid_records"] != expected["invalid_records"]:
        mismatches.append(f"Registros inválidos esperado {expected['invalid_records']}, obtenido {result['invalid_records']}.")

    for key, expected_count in expected["invalid_breakdown"].items():
        actual = int(result["validation_errors_raw"].get(key, 0))
        if actual != expected_count:
            mismatches.append(f"Inválidos '{key}' esperado {expected_count}, obtenido {actual}.")

    for key, expected_count in expected["category_counts"].items():
        actual = int(result["by_category"].get(key, 0))
        if actual != expected_count:
            mismatches.append(f"Categoría {key}: esperado {expected_count}, obtenido {actual}.")

    for key, expected_count in expected["status_counts"].items():
        actual = int(result["by_status"].get(key, 0))
        if actual != expected_count:
            mismatches.append(f"Estado {key}: esperado {expected_count}, obtenido {actual}.")

    expected_mean = expected["closed_satisfaction_mean"]
    if expected_mean is not None:
        actual_mean = result["average_satisfaction"]
        if actual_mean is None or round(actual_mean, 2) != round(expected_mean, 2):
            if actual_mean is None:
                mismatches.append(f"Satisfacción media esperada {expected_mean:.2f}, obtenida sin datos.")
            else:
                mismatches.append(f"Satisfacción media esperada {expected_mean:.2f}, obtenida {actual_mean:.2f}.")

    if mismatches:
        return ["Verificación CONTEXT-trackflow: diferencias detectadas:"] + mismatches

    return ["Verificación CONTEXT-trackflow: métricas alineadas con los valores esperados."]

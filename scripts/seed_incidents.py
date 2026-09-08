"""
Script de carga (seed) para la tabla ``incidents`` a partir del CSV histórico.

Lee el archivo ``data/raw/incidents-trackflow.csv``, transforma cada fila
a un modelo ``Incident`` usando los mapeos compartidos en
``packages/shared/schemas.py``, valida, e inserta en la base de datos
SQLAlchemy respetando idempotencia.

Uso:
    python scripts/seed_incidents.py
    # o, desde la raíz del proyecto directamente:
    cd /workspaces/... && python scripts/seed_incidents.py
"""

from __future__ import annotations

import csv
import sys
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrapping: asegurar que el monorepo raíz está en sys.path
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.shared.schemas import (
    IncidentCreate,
    OriginEnum,
    StatusEnum,
    generate_title_from_description,
    normalize_csv_branch,
    normalize_csv_category,
    normalize_csv_status,
)

# Importación adaptativa para soportar llamadas desde services/api/ o desde scripts/
if __package__:
    from .database import SessionLocal, engine
    from .models import Base, Incident
else:
    from services.api.database import SessionLocal, engine
    from services.api.models import Base, Incident

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

CSV_PATH = _REPO_ROOT / "data" / "raw" / "incidents-trackflow.csv"

# Todos los CSV_STATUS_MAP posibles se importan de schemas, pero aquí
# agregamos el mapeo adicional para "CLOSED" → StatusEnum.RESOLVED
# que ya está definido en CSV_STATUS_MAP.

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------


def parse_csv_date(raw: str | None) -> datetime | None:
    """Convierte una fecha del CSV (formato ``YYYY-MM-DD``) a datetime UTC.

    Returns ``None`` si el valor no es parseable.
    """
    if not raw or not raw.strip():
        return None
    try:
        parsed = datetime.fromisoformat(raw.strip())
        return parsed.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _row_to_dict(row: dict[str, str]) -> dict[str, Any]:
    """Transforma una fila del CSV en un diccionario listo para el ORM Incident.

    Aplica los mapeos de estado, categoría y sucursal, genera el título
    a partir de la descripción, fuerza ``origin: "customer"`` y convierte
    la fecha a UTC.  El resultado incluye tanto campos del dominio
    (title, description, …) como el campo de sistema ``created_at``.
    """
    status: StatusEnum | None = normalize_csv_status(row.get("status"))
    category: str | None = normalize_csv_category(row.get("category"))
    branch: str = normalize_csv_branch(row.get("country"))
    title: str = generate_title_from_description(row.get("description", ""))
    created_at: datetime | None = parse_csv_date(row.get("date"))

    return {
        "incident_id": (row.get("incident_id") or "").strip(),
        "title": title,
        "description": (row.get("description") or "").strip(),
        "category": category or "",
        "status": status or StatusEnum.OPEN,
        "origin": OriginEnum.CUSTOMER,  # forzado histórico
        "branch": branch,
        "created_at": created_at or datetime.now(timezone.utc),
    }


def validate_row(data: dict[str, Any]) -> tuple[bool, str | None]:
    """Valida los campos de dominio contra el esquema IncidentCreate.

    Los campos de sistema (``created_at``) se excluyen de la validación
    Pydantic porque ``IncidentCreate`` tiene ``extra="forbid"``.  La
    fecha se valida por separado comprobando que sea un datetime UTC.

    Returns:
        ``(True, None)`` si es válido, ``(False, razón_descriptiva)`` si falla.
    """
    # Extraer solo los campos que pertenecen a IncidentCreate
    pydantic_fields = {
        k: v for k, v in data.items() if k in IncidentCreate.model_fields
    }
    try:
        IncidentCreate(**pydantic_fields)
    except Exception as exc:
        # Extraer el detalle legible del ValidationError
        msg = str(exc)
        if hasattr(exc, "errors"):
            try:
                details = []
                for err in exc.errors():  # type: ignore[union-attr]
                    loc = " → ".join(str(x) for x in err.get("loc", []))
                    details.append(f"[{loc}] {err.get('msg', '')}")
                if details:
                    msg = "; ".join(details)
            except Exception:
                pass
        return False, msg

    # Validar created_at por separado
    created_at = data.get("created_at")
    if created_at is not None and not isinstance(created_at, datetime):
        return False, f"created_at debe ser un datetime, no {type(created_at).__name__}"
    if isinstance(created_at, datetime) and created_at.tzinfo is None:
        return False, "created_at debe tener zona horaria (UTC)"

    return True, None


def read_csv_rows() -> Generator[dict[str, str], None, None]:
    """Lee el CSV y genera cada fila como diccionario."""
    path = Path(CSV_PATH)
    if not path.exists():
        print(f"ERROR: No se encuentra el archivo CSV en: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        yield from reader


# ---------------------------------------------------------------------------
# Lógica principal del seed
# ---------------------------------------------------------------------------


def create_tables() -> None:
    """Crea todas las tablas definidas en los modelos SQLAlchemy si no existen."""
    Base.metadata.create_all(bind=engine)


def seed_incidents_from_csv() -> dict[str, int]:
    """Lee el CSV, valida e inserta registros en la tabla ``incidents``.

    Returns:
        Diccionario con las métricas: ``total``, ``inserted``,
        ``skipped`` (ya existen), ``errors`` (no pasan validación).
    """
    create_tables()
    session = SessionLocal()

    total = 0
    inserted = 0
    skipped = 0
    errors: list[tuple[str, str]] = []  # (incident_id, razón)

    try:
        for csv_row in read_csv_rows():
            total += 1

            # 1. Transformar CSV → dict del modelo
            data = _row_to_dict(csv_row)

            # 2. Validar contra esquema Pydantic
            is_valid, reason = validate_row(data)
            if not is_valid:
                errors.append((data["incident_id"] or f"row_{total}", reason or "Error desconocido"))
                continue

            # 3. Idempotencia: verificar si ya existe por incident_id
            if data.get("incident_id"):
                exists = session.query(
                    session.query(Incident).filter(
                        Incident.incident_id == data["incident_id"]
                    ).exists()
                ).scalar()
                if exists:
                    skipped += 1
                    continue

            # 4. Insertar
            record = Incident(**data)
            session.add(record)
            inserted += 1

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    # Reporte en consola
    _print_report(total, inserted, skipped, errors)

    return {
        "total": total,
        "inserted": inserted,
        "skipped": skipped,
        "errors": len(errors),
    }


def _print_report(
    total: int,
    inserted: int,
    skipped: int,
    errors: list[tuple[str, str]],
) -> None:
    """Imprime el resumen estructurado de la ejecución del seed."""
    border = "=" * 60
    print()
    print(border)
    print("  REPORTE DE CARGA — seed_incidents.py")
    print(border)
    print(f"  Total de registros leídos:       {total}")
    print(f"  Registros insertados:            {inserted}")
    print(f"  Registros omitidos (ya existen): {skipped}")
    print(f"  Registros descartados (errores): {len(errors)}")
    print(border)

    if errors:
        print()
        print("  DETALLE DE ERRORES POR FILA:")
        print("  " + "-" * 50)
        for idx, (row_id, reason) in enumerate(errors, 1):
            # Mostrar el mensaje legible directamente (ya viene formateado)
            if len(reason) > 120:
                short_reason = reason[:120] + "…"
            else:
                short_reason = reason
            print(f"  {idx:>3}. [{row_id}] {short_reason}")
        print()

    print(border)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    try:
        seed_incidents_from_csv()
    except Exception as exc:
        print(f"\nERROR crítico durante el seed: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
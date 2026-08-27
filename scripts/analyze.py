"""CLI principal para analizar un archivo CSV de incidentes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.api.app.services.incidents_analysis_service import (
    AnalysisServiceError,
    STATUS_LABELS_ES,
    analyze_incidents_path,
    export_analysis_csv,
    verify_against_context,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analiza un archivo CSV de incidentes.")
    parser.add_argument("csv_path", help="Ruta al archivo CSV que se analizará.")
    return parser.parse_args()


def validate_csv_path(csv_path: str) -> Path:
    path = Path(csv_path)
    if path.suffix.lower() != ".csv":
        raise ValueError("El archivo debe tener extensión .csv")
    if not path.exists():
        raise FileNotFoundError(f"El archivo no existe: {path}")
    if not path.is_file():
        raise ValueError(f"La ruta no corresponde a un archivo: {path}")
    return path


def print_summary(result: dict) -> None:
    print("\n" + "=" * 50)
    print(f"{'RESUMEN DEL ANÁLISIS':^50}")
    print("=" * 50)
    print()
    print(f"{'Total procesados:':30}{result['total_processed']:>8}")
    print(f"{'Registros válidos:':30}{result['valid_records']:>8}")
    print(f"{'Registros inválidos:':30}{result['invalid_records']:>8}")

    print("\n" + "-" * 50)
    print("REGISTROS INVÁLIDOS")
    print("-" * 50)
    if result["validation_errors"]:
        for label, value in result["validation_errors"].items():
            print(f"{label + ':':30}{value:>8}")
    else:
        print("Sin incidencias inválidas.")

    print("\n" + "-" * 50)
    print("INCIDENCIAS POR CATEGORÍA")
    print("-" * 50)
    if result["by_category"]:
        for category, value in result["by_category"].items():
            print(f"{category + ':':30}{value:>8}")
    else:
        print("Sin datos válidos para agrupar por categoría.")

    print("\n" + "-" * 50)
    print("INCIDENCIAS POR ESTADO")
    print("-" * 50)
    for status_key in ["OPEN", "CLOSED", "DISCARDED"]:
        label = STATUS_LABELS_ES.get(status_key, status_key)
        value = result["by_status"].get(status_key, 0)
        print(f"{label + ':':30}{value:>8}")

    print("\n" + "-" * 50)
    print("SATISFACCIÓN")
    print("-" * 50)
    if result["average_satisfaction"] is None:
        print("Satisfacción media: No hay datos disponibles")
    else:
        print(f"{'Satisfacción media:':30}{result['average_satisfaction']:.2f}")

    print("\n" + "=" * 50)


def print_validation_details(result: dict) -> None:
    print("\nDetalle por fila:")
    if not result["validation_error_details"]:
        print("No se detectaron errores de validación.")
        return
    for message in result["validation_error_details"]:
        print(message)


def ask_export(result: dict) -> None:
    while True:
        response = input("¿Deseas exportar los resultados a CSV? [s / n] ").strip().lower()
        if response == "s":
            csv_content = export_analysis_csv(result, header=("metric", "value"))
            Path("results.csv").write_text(csv_content, encoding="utf-8")
            print("Resultados exportados correctamente a results.csv")
            return
        if response == "n":
            return
        print("Respuesta inválida. Introduce 's' o 'n'.")


def analyze_csv(csv_path: Path) -> None:
    result = analyze_incidents_path(csv_path)

    print_validation_details(result)
    for message in verify_against_context(result):
        print(message)
    print_summary(result)
    ask_export(result)


def main() -> None:
    args = parse_args()
    try:
        csv_path = validate_csv_path(args.csv_path)
        print(f"Procesando archivo: {csv_path}")
        analyze_csv(csv_path)
    except (FileNotFoundError, ValueError, AnalysisServiceError) as error:
        print(f"Error: {error}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from ..services.incidents_analysis_service import (
    AnalysisServiceError,
    analyze_incidents_bytes,
    export_analysis_csv,
)
from ..storage.analysis_store import get_last_analysis, save_last_analysis

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/analyze")
async def analyze_incidents(file: UploadFile | None = File(default=None)) -> dict:
    if file is None:
        raise HTTPException(status_code=400, detail="No se proporcionó ningún archivo CSV.")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="El archivo no tiene un formato CSV válido.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo CSV está vacío.")

    try:
        result = analyze_incidents_bytes(content)
    except AnalysisServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error

    save_last_analysis(result)
    return result


@router.get("/results/export")
def export_results() -> Response:
    result = get_last_analysis()
    if result is None:
        raise HTTPException(status_code=404, detail="No existe un análisis previo para exportar.")

    csv_content = export_analysis_csv(result, header=("metric", "value"))
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="results.csv"'},
    )

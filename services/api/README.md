# API de análisis de incidentes

Servicio backend FastAPI para analizar CSV de incidentes TrackFlow usando la misma lógica de `analyze.py`.

## Endpoints

- `POST /api/incidents/analyze`
  - Recibe `multipart/form-data` con campo `file`.
  - Ejecuta validaciones y métricas del servicio reutilizable.
  - Guarda el último análisis en memoria del proceso.

- `GET /api/incidents/results/export`
  - Exporta el último análisis en CSV (`results.csv`).

## Persistencia del último análisis

Se usa almacenamiento en memoria de proceso (`app/storage/analysis_store.py`).

Limitación:
- Se pierde al reiniciar el proceso.
- No está compartido entre múltiples réplicas.

## Ejecución

```bash
cd services/api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
cd services/api
pytest -q
```

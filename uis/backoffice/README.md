# TrackFlow Backoffice

Interfaz para análisis de incidencias conectada al backend de `/services/api`.

## Funcionalidades

- Carga de CSV por selector y drag & drop.
- Ejecución de análisis con `POST /api/incidents/analyze`.
- Visualización de métricas y desgloses de validación.
- Descarga de resultados con `GET /api/incidents/results/export`.

## Comandos

```bash
cd uis/backoffice
npm install
npm run dev
```

Variables opcionales:

- `VITE_API_BASE_URL` (por defecto `http://localhost:8000`)

from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .routers.incidents import router as incidents_analysis_router
from .routers.incidents_crud import router as incidents_crud_router

try:
	from ..routes.auth import router as auth_router
	from ..routes.profiles import router as profiles_router
	from ..routes.users import router as users_router
except ImportError:
	from routes.auth import router as auth_router
	from routes.profiles import router as profiles_router
	from routes.users import router as users_router


def _cors_origins_from_env() -> list[str]:
	raw = os.getenv("BACKEND_CORS_ORIGINS", "")
	if raw.strip():
		return [origin.strip() for origin in raw.split(",") if origin.strip()]

	return [
		"http://localhost:5173",
		"http://127.0.0.1:5173",
		"http://localhost:5174",
		"http://127.0.0.1:5174",
	]


app = FastAPI(title="Incidents Analysis API", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=_cors_origins_from_env(),
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Handlers globales de errores
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
	_request: Request,
	exc: RequestValidationError,
) -> JSONResponse:
	"""Formatea errores de validación Pydantic en un JSON claro.

	Devuelve HTTP 422 con la lista de errores donde cada entrada
	identifica el campo problemático y el motivo, sin stack traces.
	"""
	errors = []
	for err in exc.errors():
		field = " → ".join(str(loc) for loc in err.get("loc", ()))
		errors.append({
			"field": field,
			"message": err.get("msg", "Error de validación"),
			"type": err.get("type", ""),
		})
	return JSONResponse(
		status_code=422,
		content={"detail": errors},
	)


@app.exception_handler(Exception)
async def unhandled_exception_handler(
	_request: Request,
	_exc: Exception,
) -> JSONResponse:
	"""Handler global para excepciones no capturadas.

	NUNCA expone stack traces ni detalles internos al cliente.
	"""
	return JSONResponse(
		status_code=500,
		content={"detail": "Internal server error"},
	)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# El CRUD debe incluirse ANTES que el router de análisis para que
# /api/incidents/summary tenga prioridad sobre /api/incidents/{incident_id}.
app.include_router(incidents_crud_router)
app.include_router(incidents_analysis_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)

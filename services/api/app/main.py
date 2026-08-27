from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.incidents import router as incidents_router


def _cors_origins_from_env() -> list[str]:
	raw = os.getenv("BACKEND_CORS_ORIGINS", "")
	if raw.strip():
		return [origin.strip() for origin in raw.split(",") if origin.strip()]

	return [
		"http://localhost:5173",
		"http://127.0.0.1:5173",
	]


app = FastAPI(title="Incidents Analysis API", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=_cors_origins_from_env(),
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(incidents_router)

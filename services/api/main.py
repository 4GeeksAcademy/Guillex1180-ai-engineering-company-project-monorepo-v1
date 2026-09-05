import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

if __package__:
    from .routes.auth import router as auth_router
    from .routes.profiles import router as profiles_router
    from .routes.suppliers import router as suppliers_router
    from .routes.users import router as users_router
    from .seed import run_seeder
    from .rate_limit import limiter
else:
    from routes.auth import router as auth_router
    from routes.profiles import router as profiles_router
    from routes.suppliers import router as suppliers_router
    from routes.users import router as users_router
    from seed import run_seeder
    from rate_limit import limiter


def _cors_origins_from_env() -> list[str]:
    configured_origins = os.getenv("BACKEND_CORS_ORIGINS", "")
    if configured_origins.strip():
        return [
            origin.strip()
            for origin in configured_origins.split(",")
            if origin.strip()
        ]

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_seeder()
    yield


app = FastAPI(
    title="TrackFlow Supplier Directory API",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_from_env(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(suppliers_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profiles_router)
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import verify_connectivity, close_driver
from .routers import people, experts, path, graph

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="SkillPath API",
    description="Expert-finder and introduction-path API backed by CognoDB (graph database).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(people.router)
app.include_router(experts.router)
app.include_router(path.router)
app.include_router(graph.router)


@app.exception_handler(ConnectionError)
async def connection_error_handler(request: Request, exc: ConnectionError):
    """Raised by db.run_query when CognoDB is unreachable mid-request."""
    logging.getLogger("skillpath.api").error("DB connection error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(RuntimeError)
async def config_error_handler(request: Request, exc: RuntimeError):
    """Raised by db.get_driver when connection env vars are missing."""
    logging.getLogger("skillpath.api").error("DB config error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/api/health")
def health():
    """The frontend polls this so it can show a clear 'database unreachable'
    banner instead of failing silently or throwing raw errors at the user."""
    missing = settings.validate()
    if missing:
        return JSONResponse(
            status_code=503,
            content={"status": "misconfigured", "missing_env_vars": missing},
        )
    ok, message = verify_connectivity()
    status_code = 200 if ok else 503
    return JSONResponse(status_code=status_code, content={"status": "ok" if ok else "unreachable", "message": message})


@app.on_event("shutdown")
def shutdown():
    close_driver()

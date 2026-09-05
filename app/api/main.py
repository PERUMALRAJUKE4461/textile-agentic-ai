"""FastAPI application entry point for the textile production agent."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import advanced, agent, diagnosis, machine, maintenance, research, root_cause
from app.config import load_settings


LOGGER = logging.getLogger(__name__)
settings = load_settings()

app = FastAPI(
    title="Textile Production AI Agent API",
    description="HTTP access to the existing textile machine tools and agent.",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return 400 for invalid client payloads instead of FastAPI's 422."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request data.", "errors": exc.errors()},
    )


@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    """Return a lightweight service health response."""
    return {"status": "ok", "service": "textile-production-agent"}


app.include_router(machine.router)
app.include_router(maintenance.router)
app.include_router(diagnosis.router)
app.include_router(research.router)
app.include_router(agent.router)
app.include_router(root_cause.router)
app.include_router(advanced.router)
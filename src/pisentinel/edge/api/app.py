"""FastAPI application factory (M1.4: ``GET /health`` only).

The factory never binds a socket; M1 tests drive it in-process. Serving it (interface, port,
authentication) is a later, separately approved decision (A01).
"""

from __future__ import annotations

from typing import Any

from pisentinel.config import Config
from pisentinel.edge.evidence.writer import EvidenceWriter
from pisentinel.edge.health import UNAVAILABLE, check_health


def create_app(config: Config, writer: EvidenceWriter | None) -> Any:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="PiSentinel", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health() -> JSONResponse:
        report = check_health(config, writer)
        code = 503 if report["status"] == UNAVAILABLE else 200
        return JSONResponse(report, status_code=code, headers={"Cache-Control": "no-store"})

    return app

"""Aggregates all v1 routers under a single APIRouter mounted at /api/v1."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    assets,
    attachments,
    audit,
    auth,
    dashboard,
    data,
    discovery,
    health,
    jobs,
    settings as settings_routes,
    sites,
    support_teams,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(discovery.router)
api_router.include_router(assets.router)
api_router.include_router(attachments.router)
api_router.include_router(audit.router)
api_router.include_router(dashboard.router)
api_router.include_router(jobs.router)
api_router.include_router(sites.router)
api_router.include_router(support_teams.router)
api_router.include_router(settings_routes.router)
api_router.include_router(data.router)

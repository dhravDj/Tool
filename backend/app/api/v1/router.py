"""API v1 root router combining all domain endpoint modules."""

from fastapi import APIRouter

from app.api.v1.endpoints import batches, files, health, plugins, system

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(plugins.router)
api_router.include_router(system.router)
api_router.include_router(files.router)
api_router.include_router(batches.router)

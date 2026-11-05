"""DocuMind AI Backend Application Entrypoint."""

import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger, request_id_ctx, setup_logging
from app.infrastructure.database.session import engine
from app.infrastructure.queue.redis import redis_manager
from app.infrastructure.storage.local import local_storage
from app.modules.extraction.adapters import (
    DocxExtractor,
    EPUBExtractor,
    LegacyDocExtractor,
    MarkdownExtractor,
    ODTExtractor,
    PDFExtractor,
    PlainTextExtractor,
    RTFExtractor,
)
from app.modules.files.detection.detector import universal_detector
from app.modules.image_intelligence.pipeline import image_intelligence_pipeline
from app.plugins.registry.registry import plugin_registry
from app.plugins.samples.mock_ai_provider import MockLocalAIProvider
from app.plugins.samples.mock_detector import MockTextDetectorPlugin
from app.plugins.samples.mock_extractor import MockTextExtractorPlugin
from app.plugins.samples.mock_formatter import MockMarkdownFormatter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing startup checks, plugin initialization, and shutdown."""
    # 1. Setup structured logging
    setup_logging(settings.DEBUG)
    logger.info(
        f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in [{settings.APP_ENV}] mode."
    )

    # 2. Ensure storage hierarchy is initialized
    await local_storage.initialize()
    logger.info("Storage subsystem initialized successfully.")

    # 3. Register Phase 1 & 2 plugins, Phase 3 document extractors
    plugin_registry.register(local_storage)
    plugin_registry.register(universal_detector)
    plugin_registry.register(PDFExtractor())
    plugin_registry.register(DocxExtractor())
    plugin_registry.register(LegacyDocExtractor())
    plugin_registry.register(PlainTextExtractor())
    plugin_registry.register(MarkdownExtractor())
    plugin_registry.register(RTFExtractor())
    plugin_registry.register(ODTExtractor())
    plugin_registry.register(EPUBExtractor())
    plugin_registry.register(image_intelligence_pipeline)
    plugin_registry.register(MockTextDetectorPlugin())
    plugin_registry.register(MockTextExtractorPlugin())
    plugin_registry.register(MockLocalAIProvider())
    plugin_registry.register(MockMarkdownFormatter())
    await plugin_registry.initialize_all()
    logger.info(f"Initialized {len(plugin_registry.list_plugins())} plugins in registry.")

    # 4. Check OCR Subsystem readiness
    from app.modules.extraction.ocr.router import ocr_router
    ocr_status = ocr_router.get_diagnostics()
    logger.info(
        f"OCR Subsystem Status: ready={ocr_status['is_ready']}, "
        f"adapter={ocr_status['adapter'].get('engine')}, "
        f"tesseract_installed={ocr_status['adapter'].get('is_available')}"
    )

    yield

    # 4. Graceful Shutdown
    logger.info("Shutting down DocuMind AI platform...")
    await plugin_registry.shutdown_all()
    await redis_manager.close()
    await engine.dispose()
    logger.info("Database and background resources released.")


def create_application() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Universal File Intelligence Platform — Phase 1 Backend API",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 1. Request ID and Correlation Middleware
    @app.middleware("http")
    async def request_correlation_middleware(request: Request, call_next) -> Response:  # type: ignore
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(req_id)
        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
            process_time = time.perf_counter() - start_time
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"
            return response
        finally:
            request_id_ctx.reset(token)

    # 2. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS
        if isinstance(settings.BACKEND_CORS_ORIGINS, list)
        else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Exception Handlers
    register_exception_handlers(app)

    # 4. API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    async def root_index() -> JSONResponse:
        return JSONResponse(
            content={
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.APP_ENV,
                "status": "online",
                "docs_url": "/docs",
                "api_v1": f"{settings.API_V1_STR}/health",
            }
        )

    return app


app = create_application()

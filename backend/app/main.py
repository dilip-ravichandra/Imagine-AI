import logging
import secrets
import threading
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from ai_engine.prompt import PromptAnalysis, analyze_prompt

from .config import Settings, load_settings
from .schemas.model import AdapterStatus, ModelInfoResponse
from .schemas.prompt import PromptAnalysisRequest
from .schemas.v1 import (API_VERSION, CapabilitiesResponse, ErrorBody, ErrorResponse,
                         GenerateRequest, GenerateResponse, HealthResponse)
from .services.adaptive import build_controller
from .services.engine import DiffusionEngine, SDTurboEngine
from .services.errors import ServiceError
from .services.generation import GenerationService
from .services.storage import ImageStore

log = logging.getLogger("imagineai")


def _err(status_code: int, code: str, message: str, retryable: bool, action: str, rid=None):
    body = ErrorResponse(request_id=rid, error=ErrorBody(
        code=code, message=message, retryable=retryable, suggested_action=action))
    return JSONResponse(status_code=status_code, content=body.model_dump())


def create_app(engine: Optional[DiffusionEngine] = None, settings: Optional[Settings] = None,
               controller=None, monitor=None) -> FastAPI:
    settings = settings or load_settings()
    engine = engine or SDTurboEngine(settings)
    store = ImageStore(settings.output_dir, settings.max_stored_images)
    if controller is None:  # P6: stays None unless ADAPTIVE_PROFILE is configured
        controller, monitor = build_controller(settings)
    service = GenerationService(engine, store, settings, controller, monitor)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        engine.adapter_status()  # logs a clear warning at startup if a configured adapter will not be used
        if settings.preload_model:
            threading.Thread(target=_safe_preload, args=(service,), daemon=True).start()
        yield

    def require_api_key(request: Request) -> None:
        """No-op unless API_KEY is configured. Constant-time compare; the supplied value is never logged or echoed."""
        if not settings.api_key:
            return
        supplied = request.headers.get("x-api-key", "")
        if not secrets.compare_digest(supplied.encode("utf-8"), settings.api_key.encode("utf-8")):
            raise ServiceError(401, "UNAUTHORIZED", "A valid API key is required.", False,
                               "Send the server's API key in the X-API-Key header.")

    auth = [Depends(require_api_key)]
    app = FastAPI(title="Imagine AI", version=API_VERSION, lifespan=lifespan)
    app.mount("/images", StaticFiles(directory=str(store.directory)), name="images")

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return _err(422, "INVALID_REQUEST", "Request failed validation.", False,
                    "Check prompt (1-500 chars), quality_mode (quick|balanced|best), resolution (256-1024), seed.")

    @app.exception_handler(ServiceError)
    async def service_handler(request: Request, exc: ServiceError):
        return _err(exc.status, exc.code, exc.message, exc.retryable, exc.action,
                    rid=getattr(request.state, "request_id", None))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        log.error("unhandled error", exc_info=exc)  # details stay in server logs only
        return _err(500, "INTERNAL_ERROR", "An unexpected error occurred.", True, "Retry later.",
                    rid=getattr(request.state, "request_id", None))

    @app.get("/health", response_model=HealthResponse)
    def health():
        return HealthResponse()

    @app.get("/api/v1/capabilities", response_model=CapabilitiesResponse, dependencies=auth)
    def capabilities():
        ok, _ = engine.availability()
        res = settings.supported_resolutions
        return CapabilitiesResponse(quality_modes=["quick", "balanced", "best"],
                                    min_resolution=min(res), max_resolution=max(res),
                                    generation_available=ok, deployment_mode="hybrid/cloud")

    @app.get("/api/v1/model", response_model=ModelInfoResponse, dependencies=auth)
    def model_info():
        """Additive (P3B): which model/adapter this server will use or is using. No GPU work, no paths."""
        return ModelInfoResponse(model=settings.model_id, model_revision=settings.model_revision,
                                 loaded=engine.is_loaded(), adapter=AdapterStatus(**engine.adapter_status()))

    @app.post("/api/v1/generate", response_model=GenerateResponse, dependencies=auth)
    def generate(req: GenerateRequest, request: Request):
        # sync endpoint -> runs in the threadpool, so /health stays responsive during generation
        rid = uuid.uuid4().hex
        request.state.request_id = rid
        return service.generate(req, str(request.base_url), rid)

    @app.post("/api/v1/prompt/analysis", response_model=PromptAnalysis, dependencies=auth)
    def prompt_analysis(req: PromptAnalysisRequest):
        """Additive (P2): structured analysis of the prompt TEXT. Does not touch the model or the GPU."""
        return analyze_prompt(req.prompt)

    return app


def _safe_preload(service: GenerationService) -> None:
    try:
        service.preload()
    except Exception:  # noqa: BLE001
        log.exception("preload failed; the model will be retried on the first request")


app = create_app()

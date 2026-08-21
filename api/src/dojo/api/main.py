from asyncio import Lock
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from dojo.api.e2e import router as e2e_router
from dojo.api.health import router as health_router
from dojo.api.routes import router as api_router
from dojo.api.settings import Settings, get_settings
from dojo.e2e import fixed_e2e_clock
from dojo.google import OAuthTokenStore
from dojo.service import DojoService


def create_app(app_settings: Settings | None = None) -> FastAPI:
    settings = app_settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = settings
        clock = fixed_e2e_clock() if settings.app_env == "e2e" else None
        app.state.dojo_service = DojoService(settings.duckdb_path, clock=clock)
        if settings.app_env == "e2e":
            app.state.e2e_active_database = Path(settings.duckdb_path).resolve()
        app.state.oauth_token_store = OAuthTokenStore()
        if settings.app_env == "e2e":
            app.state.e2e_reset_lock = Lock()
        try:
            yield
        finally:
            service = getattr(app.state, "dojo_service", None)
            if service is not None:
                service.close()

    app = FastAPI(title="dojo", lifespan=lifespan)
    if settings.app_env == "e2e":

        @app.middleware("http")
        async def coordinate_e2e_service_access(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            if request.url.path == "/__e2e/reset":
                return await call_next(request)
            async with request.app.state.e2e_reset_lock:
                return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
    app.include_router(health_router)
    app.include_router(api_router)
    if (
        settings.app_env == "e2e"
        and settings.e2e_reset_token
        and settings.e2e_baseline_dir
        and settings.e2e_run_dir
    ):
        app.include_router(e2e_router)
    return app


app = create_app()

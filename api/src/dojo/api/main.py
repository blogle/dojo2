from asyncio import Lock
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from dojo.api.e2e import router as e2e_router
from dojo.api.health import router as health_router
from dojo.api.routes import router as api_router
from dojo.api.settings import Settings, get_settings
from dojo.e2e import fixed_e2e_clock
from dojo.google import OAuthTokenStore
from dojo.service import DojoService


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and "." not in Path(path).name:
                return await super().get_response("index.html", scope)
            raise


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
    frontend_dir = Path("/share/dojo")
    if frontend_dir.is_dir():
        app.mount("/", SPAStaticFiles(directory=frontend_dir, html=True), name="frontend")
    return app


app = create_app()

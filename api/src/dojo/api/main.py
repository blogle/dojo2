from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from dojo.api.health import router as health_router
from dojo.api.routes import router as api_router
from dojo.api.settings import get_settings
from dojo.google import OAuthTokenStore
from dojo.service import DojoService

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = settings
    app.state.dojo_service = DojoService(settings.duckdb_path)
    app.state.oauth_token_store = OAuthTokenStore()
    try:
        yield
    finally:
        service = getattr(app.state, "dojo_service", None)
        if service is not None:
            service.close()


def create_app() -> FastAPI:
    app = FastAPI(title="dojo", lifespan=lifespan)
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
    return app


app = create_app()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from dojo.api.health import router as health_router
from dojo.api.routes import router as api_router
from dojo.api.settings import get_settings
from dojo.google import OAuthTokenStore
from dojo.service import DojoService

settings = get_settings()

app = FastAPI(title="dojo")
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


@app.on_event("startup")
def startup() -> None:
    app.state.settings = settings
    app.state.dojo_service = DojoService(settings.duckdb_path)
    app.state.oauth_token_store = OAuthTokenStore()


@app.on_event("shutdown")
def shutdown() -> None:
    service = getattr(app.state, "dojo_service", None)
    if service is not None:
        service.close()

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "dojo"}


@router.get("/api/app/status")
def app_status() -> dict[str, str | bool]:
    return {"app": "dojo", "ready": False, "mode": "skeleton"}

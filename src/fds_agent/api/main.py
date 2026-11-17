from fastapi import FastAPI

from fds_agent.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """프로세스 상태만 반환하며 DB·모델 준비 여부는 보장하지 않는다."""
    return {"status": "ok", "environment": settings.environment}

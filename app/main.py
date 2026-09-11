from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Shared backend for the Roamly travel planner.",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    """Liveness probe — confirms the API process is up."""
    return {
    "status": "ok",
    "service": "roamly-api",
    "environment": settings.ENVIRONMENT,
    }

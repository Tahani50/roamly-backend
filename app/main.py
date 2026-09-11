from fastapi import FastAPI

app = FastAPI(
    title="Roamly API",
    description="Shared backend for the Roamly travel planner.",
    version="0.1.0",
)


@app.get("/health", tags=["System"])
async def health() -> dict[str, str]:
    """Liveness probe — confirms the API process is up."""
    return {"status": "ok", "service": "roamly-api"}

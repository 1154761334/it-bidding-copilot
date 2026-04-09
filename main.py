from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.core.config import settings
from api.core.database import engine
from api.core.logger import get_logger
from api.routers import config_v2, dashboard_v2, drafting_v2, enterprise_v2, rfp_v2

logger = get_logger("root")
API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API application")
    yield
    logger.info("Stopping API application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": settings.APP_NAME, "status": "operational"}


@app.get("/healthz")
async def healthz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:
        logger.exception("Health check failed")
        return {"status": "degraded", "database": "unreachable", "detail": str(exc)}


# Unified API v1 registration
for base_prefix in (API_V1_PREFIX,):
    app.include_router(rfp_v2.router, prefix=f"{base_prefix}/rfp", tags=["RFP Analysis"])
    app.include_router(enterprise_v2.router, prefix=f"{base_prefix}/enterprise", tags=["Enterprise Assets"])
    app.include_router(drafting_v2.router, prefix=f"{base_prefix}/bid", tags=["Bidding & Drafting"])
    app.include_router(config_v2.router, prefix=f"{base_prefix}/config", tags=["System Config"])
    app.include_router(dashboard_v2.router, prefix=f"{base_prefix}/dashboard", tags=["Dashboard Stats"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

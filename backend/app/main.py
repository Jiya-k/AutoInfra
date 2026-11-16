import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import (
    Base,
    check_database_connection,
    engine
)
from app.models.server import Server
from app.api.servers import router as servers_router


# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )
)

logger = logging.getLogger("autoinfra")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    logger.info("Starting AutoInfra application")

    try:
        check_database_connection()
        Base.metadata.create_all(bind=engine)

        logger.info("Database connection successful")
        logger.info("Database tables initialized")

    except Exception:
        logger.exception("Application startup failed")
        raise

    yield

    engine.dispose()
    logger.info("Database connections closed")
    logger.info("AutoInfra application stopped")


app = FastAPI(
    title="AutoInfra API",
    description="Cloud Infrastructure Automation and Management Platform",
    version="0.3.0",
    lifespan=lifespan
)

app.include_router(servers_router)


@app.get("/")
async def root():
    return {
        "application": "AutoInfra",
        "message": "Infrastructure Automation Platform is running",
        "version": "0.3.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": "AutoInfra"
    }


@app.get("/health/db")
async def database_health_check():
    try:
        check_database_connection()

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception:
        logger.exception("Database health check failed")

        return {
            "status": "unhealthy",
            "database": "disconnected"
        }

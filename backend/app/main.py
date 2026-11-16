from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import check_database_connection, engine

from app.core.database import Base, check_database_connection, engine
from app.models.server import Server
from app.api.servers import router as servers_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify database connectivity during application startup
    check_database_connection()

    Base.metadata.create_all(bind=engine)

    print("AutoInfra database connection successful!")
    print("AutoInfra database tables initialized!")

    yield

    # Close database connections during shutdown
    engine.dispose()
    print("AutoInfra database connections closed.")


app = FastAPI(
    title="AutoInfra API",
    description="Cloud Infrastructure Automation and Management Platform",
    version="0.2.0",
    lifespan=lifespan
)
app.include_router(servers_router)

@app.get("/")
async def root():
    return {
        "application": "AutoInfra",
        "message": "Infrastructure Automation Platform is running",
        "version": "0.2.0"
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
        return {
            "status": "unhealthy",
            "database": "disconnected"
        }

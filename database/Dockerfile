FROM postgres:17

LABEL org.opencontainers.image.title="AutoInfra PostgreSQL Database"
LABEL org.opencontainers.image.description="PostgreSQL database service for AutoInfra"

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"

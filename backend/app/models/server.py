
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint
)

from app.core.database import Base


class Server(Base):
    __tablename__ = "servers"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "region",
            "instance_id",
            name="uq_server_provider_region_instance"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)

    instance_id = Column(String(100), nullable=True)
    region = Column(String(50), nullable=True)

    private_ip = Column(String(45), nullable=True)
    public_ip = Column(String(45), nullable=True)

    status = Column(String(30), nullable=False, default="unknown")
    operating_system = Column(String(50), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

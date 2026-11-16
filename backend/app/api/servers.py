from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import SessionLocal
from app.models.server import Server
from ipaddress import ip_address
from pydantic import field_validator, Field
from app.services.aws_discovery import discover_ec2_instances

router = APIRouter(prefix="/servers", tags=["Servers"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider: str
    instance_id: str | None = Field(default=None, max_length=100)
    region: str | None = Field(default=None, max_length=50)
    private_ip: str | None = None
    public_ip: str | None = None
    status: str = "unknown"
    operating_system: str | None = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Server name cannot be empty")

        return value

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value):
        allowed_providers = {"aws", "azure"}

        value = value.strip().lower()

        if value not in allowed_providers:
            raise ValueError("Provider must be AWS or Azure")

        return value.upper()

    @field_validator("status")
    @classmethod
    def validate_status(cls, value):
        allowed_statuses = {
            "running",
            "stopped",
            "pending",
            "terminated",
            "unknown"
        }

        value = value.strip().lower()

        if value not in allowed_statuses:
            raise ValueError("Invalid server status")

        return value

    @field_validator("private_ip", "public_ip")
    @classmethod
    def validate_ip_address(cls, value):
        if value is not None:
            try:
                ip_address(value)
            except ValueError:
                raise ValueError("Invalid IP address")

        return value



class ServerResponse(ServerCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)



@router.post("/", response_model=ServerResponse, status_code=201)
def create_server(server_data: ServerCreate, db: Session = Depends(get_db)):
    server = Server(**server_data.model_dump())

    try:
        db.add(server)
        db.commit()
        db.refresh(server)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A server with this provider, region, and instance ID already exists"
        )

    return server



@router.get("/", response_model=list[ServerResponse])
def get_servers(db: Session = Depends(get_db)):
    return db.query(Server).order_by(Server.id).all()


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()

    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    return server

@router.delete("/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()

    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    db.delete(server)
    db.commit()

    return {
        "message": "Server deleted successfully",
        "server_id": server_id
    }


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    server_data: ServerCreate,
    db: Session = Depends(get_db)
):
    server = db.query(Server).filter(Server.id == server_id).first()

    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    update_data = server_data.model_dump()

    for field, value in update_data.items():
        setattr(server, field, value)

    db.commit()
    db.refresh(server)

    return server


@router.post("/discover/aws")
def discover_aws_servers(
    region: str = "ap-south-1",
    db: Session = Depends(get_db)
):
    """
    Discover AWS EC2 instances and synchronize them
    with the AutoInfra PostgreSQL inventory.
    """

    try:
        instances = discover_ec2_instances(region=region)

        if not instances:
            return {
                "message": "No EC2 instances found in AWS",
                "region": region,
                "discovered": 0,
                "created": 0,
                "updated": 0
            }

        created = 0
        updated = 0

        for instance_data in instances:

            # Match an existing AWS instance by its unique identity.
            existing_server = db.query(Server).filter(
                Server.provider == "AWS",
                Server.region == instance_data["region"],
                Server.instance_id == instance_data["instance_id"]
            ).first()

            # Keep only statuses supported by our inventory API.
            allowed_statuses = {
                "running", "stopped", "pending", "terminated"
            }

            if instance_data["status"] not in allowed_statuses:
                instance_data["status"] = "unknown"

            if existing_server:
                for field, value in instance_data.items():
                    setattr(existing_server, field, value)

                updated += 1

            else:
                new_server = Server(**instance_data)
                db.add(new_server)
                created += 1

        db.commit()

        return {
            "message": "AWS EC2 discovery and inventory sync completed",
            "region": region,
            "discovered": len(instances),
            "created": created,
            "updated": updated
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="AWS EC2 discovery or inventory synchronization failed"
        )

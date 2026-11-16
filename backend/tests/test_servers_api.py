import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base
from app.api.servers import get_db
from app.services.aws_discovery import discover_ec2_instances


@pytest.fixture
def test_db():
    """Create an isolated in-memory SQLite database."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def client(test_db):
    """Override the application's database dependency."""

    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_and_retrieve_server(client):
    """Verify that a server can be created and retrieved."""

    payload = {
        "name": "test-ec2-server",
        "provider": "AWS",
        "instance_id": "i-test123",
        "region": "ap-south-1",
        "private_ip": "10.0.1.10",
        "public_ip": None,
        "status": "running",
        "operating_system": "Linux/UNIX"
    }

    create_response = client.post("/servers/", json=payload)

    assert create_response.status_code == 201
    assert create_response.json()["name"] == "test-ec2-server"

    server_id = create_response.json()["id"]

    get_response = client.get(f"/servers/{server_id}")

    assert get_response.status_code == 200
    assert get_response.json()["instance_id"] == "i-test123"


def test_aws_discovery_inserts_new_instances(client, monkeypatch):
    """Verify that discovered AWS instances are inserted."""

    discovered_instances = [
        {
            "name": "discovered-server",
            "provider": "AWS",
            "instance_id": "i-new123",
            "region": "ap-south-1",
            "private_ip": "10.0.2.10",
            "public_ip": None,
            "status": "running",
            "operating_system": "Linux/UNIX"
        }
    ]

    monkeypatch.setattr(
        "app.api.servers.discover_ec2_instances",
        lambda region: discovered_instances
    )

    response = client.post("/servers/discover/aws?region=ap-south-1")

    assert response.status_code == 200
    assert response.json()["discovered"] == 1
    assert response.json()["created"] == 1
    assert response.json()["updated"] == 0

    inventory = client.get("/servers/").json()

    assert len(inventory) == 1
    assert inventory[0]["instance_id"] == "i-new123"


def test_aws_discovery_updates_existing_instances(client, monkeypatch):
    """Verify that existing instances are updated, not duplicated."""

    payload = {
        "name": "old-server-name",
        "provider": "AWS",
        "instance_id": "i-existing123",
        "region": "ap-south-1",
        "private_ip": "10.0.3.10",
        "public_ip": None,
        "status": "stopped",
        "operating_system": "Linux/UNIX"
    }

    client.post("/servers/", json=payload)

    discovered_instances = [
        {
            "name": "updated-server-name",
            "provider": "AWS",
            "instance_id": "i-existing123",
            "region": "ap-south-1",
            "private_ip": "10.0.3.20",
            "public_ip": None,
            "status": "running",
            "operating_system": "Linux/UNIX"
        }
    ]

    monkeypatch.setattr(
        "app.api.servers.discover_ec2_instances",
        lambda region: discovered_instances
    )

    response = client.post("/servers/discover/aws?region=ap-south-1")

    assert response.status_code == 200
    assert response.json()["created"] == 0
    assert response.json()["updated"] == 1

    inventory = client.get("/servers/").json()

    assert len(inventory) == 1
    assert inventory[0]["name"] == "updated-server-name"
    assert inventory[0]["private_ip"] == "10.0.3.20"
    assert inventory[0]["status"] == "running"


def test_empty_discovery_preserves_existing_inventory(client, monkeypatch):
    """Verify that empty discovery doesn't delete existing records."""

    payload = {
        "name": "manual-server",
        "provider": "AWS",
        "instance_id": "i-manual123",
        "region": "ap-south-1",
        "private_ip": "10.0.4.10",
        "public_ip": None,
        "status": "stopped",
        "operating_system": "Ubuntu 24.04"
    }

    client.post("/servers/", json=payload)

    monkeypatch.setattr(
        "app.api.servers.discover_ec2_instances",
        lambda region: []
    )

    response = client.post("/servers/discover/aws?region=ap-south-1")

    assert response.status_code == 200
    assert response.json()["discovered"] == 0

    inventory = client.get("/servers/").json()

    assert len(inventory) == 1
    assert inventory[0]["instance_id"] == "i-manual123"


def test_aws_discovery_failure_returns_502(client, monkeypatch):
    """Verify that AWS failures trigger rollback and a safe response."""

    monkeypatch.setattr(
        "app.api.servers.discover_ec2_instances",
        lambda region: (_ for _ in ()).throw(
            RuntimeError("Simulated AWS failure")
        )
    )

    response = client.post("/servers/discover/aws?region=ap-south-1")

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "AWS EC2 discovery or inventory synchronization failed"
    )

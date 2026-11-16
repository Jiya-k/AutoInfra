
# AutoInfra – AWS Infrastructure Discovery Platform

AutoInfra is a full-stack infrastructure management application that discovers and displays AWS EC2 instances across multiple AWS regions.

The project demonstrates containerization, multi-container orchestration, cloud deployment, AWS IAM-based authentication, persistent database storage, application health checks, and centralized container logging.

## Project Objectives

- Containerize a full-stack application.
- Build separate Docker images for the frontend, backend, and database.
- Use Docker Compose to orchestrate services and networking.
- Deploy the application on an AWS EC2 instance.
- Configure AWS networking and security groups.
- Integrate AWS EC2 discovery using IAM role authentication.
- Implement health checks, logging, and persistent database storage.

## Architecture

AutoInfra consists of three containerized services:

| Component | Technology | Responsibility |
|---|---|---|
| Frontend | React, Vite, Nginx | User interface and API reverse proxy |
| Backend | Python, FastAPI, Boto3 | REST APIs and AWS EC2 discovery |
| Database | PostgreSQL 17 | Persistent infrastructure inventory |

### Application Architecture

```text
                 Internet
                    |
                    v
             AWS EC2 Instance
                    |
              Port 80 (HTTP)
                    |
                    v
             Frontend Container
              React + Nginx
                    |
              /api reverse proxy
                    |
                    v
             Backend Container
                FastAPI
                    |
           +--------+--------+
           |                 |
           v                 v
      PostgreSQL          AWS APIs
       Container        (Boto3 / IAM)
           |                 |
           v                 v
     Persistent Volume   EC2 Discovery
```

All three services communicate through a dedicated Docker bridge network.

The PostgreSQL database and backend API are not directly exposed to the public internet.

## Technology Stack

- Frontend: React, Vite, Nginx
- Backend: Python, FastAPI
- Database: PostgreSQL 17
- Containerization: Docker
- Orchestration: Docker Compose
- Cloud Platform: AWS
- Infrastructure: Amazon EC2, VPC, Subnet, Internet Gateway, Route Table, Security Groups
- AWS Integration: Boto3 and IAM instance role
- Operating System: Ubuntu Linux

## Repository Structure

```text
AutoInfra/
├── automation/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   └── Dockerfile
├── docker/
├── docs/
├── front/
│   ├── public/
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

- Docker Engine
- Docker Compose plugin
- AWS account
- AWS EC2 instance running Ubuntu
- An IAM role attached to the EC2 instance with permission to discover EC2 resources

## Environment Configuration

Clone the repository:

```bash
git clone https://github.com/Jiya-k/AutoInfra.git
cd AutoInfra
```

Create the environment file:

```bash
cp .env.example .env
```

Edit the configuration:

```bash
nano .env
```

Configure the following variables:

| Variable | Description |
|---|---|
| APP_NAME | Application name |
| APP_ENV | Application environment |
| APP_PORT | Backend application port |
| AWS_REGION | AWS region |
| AWS_DEFAULT_REGION | Default Boto3 region |
| POSTGRES_DB | PostgreSQL database name |
| POSTGRES_USER | PostgreSQL username |
| POSTGRES_PASSWORD | PostgreSQL password |
| DATABASE_URL | SQLAlchemy database connection string |
| SECRET_KEY | Application secret key |

Use strong, unique values for the database password and secret key.

The password in DATABASE_URL must match POSTGRES_PASSWORD.

Never commit `.env` or AWS credentials to GitHub.

## AWS IAM Configuration

AutoInfra uses the EC2 instance's attached IAM role to authenticate with AWS.

No AWS access keys need to be stored inside the production containers.

The IAM role requires permission to:

- `ec2:DescribeRegions`
- `ec2:DescribeInstances`

Attach the IAM role to the EC2 instance before starting AWS discovery.

## Docker Deployment

Build and start all services:

```bash
docker compose up --build -d
```

Check container status:

```bash
docker compose ps
```

View frontend logs:

```bash
docker compose logs frontend
```

View backend logs:

```bash
docker compose logs backend
```

View database logs:

```bash
docker compose logs db
```

Follow logs continuously:

```bash
docker compose logs -f
```

## Application Access

Once the containers are running, access AutoInfra using:

```text
http://<EC2-PUBLIC-IP>
```

The frontend is exposed on port 80.

The backend and PostgreSQL services communicate internally through the Docker network.

## Health Checks

AutoInfra includes container-level health checks.

The frontend health check verifies that Nginx serves the application.

The backend health check verifies the FastAPI health endpoint.

The database health check uses PostgreSQL's `pg_isready` utility.

Application health endpoints:

```text
GET /health
GET /health/db
```

Through the frontend reverse proxy:

```text
http://<EC2-PUBLIC-IP>/api/health
http://<EC2-PUBLIC-IP>/api/health/db
```

Check health status:

```bash
docker compose ps
```

## AWS EC2 Discovery

AutoInfra can discover EC2 instances across available AWS regions.

Trigger discovery using:

```bash
curl -X POST http://localhost/api/servers/discover/aws/all-regions
```

The discovery process:

1. Retrieves available AWS regions.
2. Connects to the EC2 API in each region.
3. Retrieves EC2 instance details.
4. Synchronizes discovered instances with the PostgreSQL inventory.
5. Returns a discovery summary, including successful and failed regions.

The application displays discovered infrastructure in its dashboard.

## Database Persistence

PostgreSQL uses a named Docker volume:

```yaml
volumes:
  postgres-data:
```

This ensures database data persists when containers are restarted or recreated without deleting the volume.

Restart the services:

```bash
docker compose restart
```

Verify that the application and inventory are still available:

```bash
docker compose ps
curl http://localhost/api/servers/
```

**Important:** Avoid using `docker compose down -v` when you want to preserve database records. The `-v` option deletes the associated named volumes.

## Networking and Security

The AWS deployment uses a public subnet connected to an Internet Gateway.

The EC2 security group is configured with:

| Port | Protocol | Source | Purpose |
|---|---|---|---|
| 22 | TCP | Restricted administrator IP | SSH access |
| 80 | TCP | 0.0.0.0/0 | HTTP application access |

Backend port 8000 and PostgreSQL port 5432 are not exposed through the EC2 security group.

## Testing

The backend includes automated tests.

Run the tests inside the backend environment:

```bash
pytest -v
```

The application was also verified through actual AWS deployment, container health checks, database connectivity, and multi-region EC2 discovery.

## Troubleshooting

### Check container status

```bash
docker compose ps
```

### Inspect backend logs

```bash
docker compose logs --tail=100 backend
```

### Inspect database logs

```bash
docker compose logs --tail=100 db
```

### Validate Docker Compose configuration

```bash
docker compose config --quiet
```

### Check application health

```bash
curl http://localhost/api/health
curl http://localhost/api/health/db
```

### Check discovered infrastructure

```bash
curl http://localhost/api/servers/
```

## Security Considerations

- Use IAM roles instead of storing AWS access keys in production containers.
- Keep `.env` and private credentials out of source control.
- Restrict SSH access to trusted IP addresses.
- Do not expose PostgreSQL or backend application ports publicly.
- Use strong database credentials and application secrets.
- Use HTTPS and appropriate access controls before exposing the application beyond a demonstration environment.

## Project Status

The application has been deployed and tested on AWS EC2.

Verified capabilities include:

- Full-stack Docker containerization.
- Docker Compose orchestration.
- AWS EC2 deployment.
- Multi-region EC2 discovery.
- IAM role-based AWS authentication.
- PostgreSQL data persistence across container restarts.
- Container health checks.
- Application and service logging.

## Author

**AutoInfra – Docker, AWS and Real-World DevOps Deployment**

GitHub: https://github.com/Jiya-k/AutoInfra

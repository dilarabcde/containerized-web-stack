# Containerized Web Stack

A hands-on DevOps project demonstrating how a multi-container web application can be built and operated with Docker and Docker Compose.

## Stack

- Flask web application
- PostgreSQL 16
- Docker
- Docker Compose
- Docker networking and service discovery
- Persistent Docker volumes
- Application and database healthchecks
- Container restart policy
- Environment-based configuration

## Architecture

```text
Client
  |
  | localhost:8080
  v
Flask Web App
  |
  | DB_HOST=db
  | Docker DNS
  v
PostgreSQL
  |
  v
postgres-data
Persistent Docker Volume
```

Docker Compose creates an internal network where the `web-app` service can reach PostgreSQL using the service name `db`.

PostgreSQL data is stored in the external `postgres-data` volume so the data lifecycle is independent from the container lifecycle.

## Configuration

Create the local environment file from the provided template:

```bash
cp .env.example .env
```

The `.env` file is excluded from Git and should not be committed.

## Run

Start the stack:

```bash
docker compose up -d
```

Check container and health status:

```bash
docker compose ps
```

Test the application:

```bash
curl http://localhost:8080
```

Test application and database health:

```bash
curl -i http://localhost:8080/health
```

View logs:

```bash
docker compose logs
```

Stop and remove the Compose stack:

```bash
docker compose down
```

## Health and Recovery

The PostgreSQL service includes a healthcheck.

The web application waits for the database to become healthy before starting and exposes its own `/health` endpoint.

The web application also uses a container restart policy:

```text
unless-stopped
```

This provides basic service recovery when the application process exits unexpectedly.

## Persistence

Database files are stored in the external Docker volume:

```text
postgres-data
```

Running:

```bash
docker compose down
```

removes the application containers and Compose network, while the external database volume remains available for future containers.

## Project Goal

This project demonstrates the core operational concepts behind a containerized multi-service application:

```text
Image
  ↓
Container
  ↓
Docker Network
  ↓
Service Discovery
  ↓
Environment Configuration
  ↓
Persistent Storage
  ↓
Healthchecks
  ↓
Restart / Recovery
  ↓
Docker Compose Lifecycle
```

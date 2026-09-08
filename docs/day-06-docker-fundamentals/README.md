# Containerized Web Stack

A hands-on DevOps project demonstrating how a Flask web application and PostgreSQL database can run as a multi-container stack using Docker and Docker Compose.

## Architecture

```text
Client (Mac)
     |
     | HTTP :8080
     v
+------------------+
|     web-app      |
|      Flask       |
|   0.0.0.0:8080   |
+--------+---------+
         |
         | DB_HOST=db
         | PostgreSQL :5432
         v
+------------------+
|        db        |
|  PostgreSQL 16   |
+--------+---------+
         |
         v
+------------------+
|  postgres-data   |
|  Docker Volume   |
+------------------+
```

## Technologies

- Docker
- Docker Compose
- Python 3.12
- Flask
- PostgreSQL 16

## Docker Image

The Flask application is packaged using a Dockerfile.

The image uses `python:3.12-slim`, installs dependencies from `requirements.txt`, copies the application into the image, and starts the Flask application.

```bash
docker build -t containerized-web-stack .
```

## Container Networking

The Flask application and PostgreSQL run in separate containers.

Docker networking allows the application to connect to PostgreSQL using the service name:

```text
DB_HOST=db
```

The application does not need to know the database container's IP address.

Docker's internal DNS resolves the service name `db` to the appropriate container.

The PostgreSQL port does not need to be published to the host because communication between the application and database happens inside the Docker network.

## Environment Variables

Database configuration is passed to the application through environment variables:

```text
DB_HOST=db
DB_PORT=5432
DB_NAME=appdb
DB_USER=appuser
DB_PASSWORD=apppassword
```

This separates runtime configuration from application code.

The credentials used in this repository are lab credentials only and should not be used for production systems.

## Persistent Storage

PostgreSQL data is stored using a named Docker volume:

```text
postgres-data
```

The volume is mounted to:

```text
/var/lib/postgresql/data
```

This separates the lifecycle of the database container from the lifecycle of the database data.

During testing, the PostgreSQL container was deleted and recreated while the data stored in the volume remained available.

## Docker Compose

Initially, the Flask and PostgreSQL containers were created manually using separate `docker run` commands.

Docker Compose was then introduced to describe the complete stack declaratively in a single `compose.yaml` file.

The stack can now be started with:

```bash
docker compose up -d
```

Its status can be checked with:

```bash
docker compose ps
```

And stopped with:

```bash
docker compose down
```

## Database Healthcheck

A PostgreSQL healthcheck verifies that the database is ready to accept connections:

```text
pg_isready -U appuser -d appdb -p 5432
```

The Flask application depends on the database becoming healthy before it starts.

This demonstrates an important distinction:

```text
Container running != Service healthy
```

A container process may be running even when the service inside it is not ready to serve requests.

## Troubleshooting Lab

Several failures were intentionally introduced and diagnosed during the project.

### Invalid YAML configuration

A malformed healthcheck definition caused Docker Compose to fail before containers could be managed.

The configuration was inspected using:

```bash
docker compose config
```

This demonstrated that troubleshooting should begin at the configuration layer before investigating containers or applications.

### Failed database healthcheck

The PostgreSQL healthcheck was intentionally configured to check port `9999` instead of the actual PostgreSQL port `5432`.

Docker reported the database container as unhealthy and prevented the dependent web application from starting.

The issue was investigated using:

```bash
docker compose ps
docker inspect containerized-web-stack-db-1
docker compose logs db
```

The PostgreSQL logs showed that the database was correctly listening on port `5432`, while the healthcheck was testing port `9999`.

After correcting the healthcheck, the database became healthy and the web application started successfully.

## Verification

The complete request path was tested with:

```bash
curl http://localhost:8080
```

The successful response confirmed the complete flow:

```text
Client
  ↓
Host port 8080
  ↓
Flask container
  ↓
Docker DNS
  ↓
PostgreSQL container
  ↓
Database response
```

## Key Lessons

- A Dockerfile defines how an image is built.
- Docker Compose defines how multiple containers work together.
- Containers communicate through Docker networks.
- Service names can be used for container-to-container DNS resolution.
- Environment variables provide runtime configuration.
- Named volumes keep persistent data separate from container lifecycle.
- `docker compose down` can remove containers and networks without deleting persistent external volumes.
- A running container is not necessarily a healthy service.
- Healthchecks can be used to control service dependencies.
- Logs, container state, health information, and configuration validation are key troubleshooting tools.

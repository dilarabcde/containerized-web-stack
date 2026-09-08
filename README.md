# Containerized Web Stack

A hands-on DevOps project focused on containerizing a simple Flask web application with Docker.

This project is part of my practical DevOps learning journey. The goal is not only to run an application inside a container, but also to understand how Docker images, containers, dependencies, networking, ports, logs, caching, and image versioning work together.

## Day 6 - Docker Fundamentals

### What I Built

I created a simple Flask web application and packaged it into a Docker image.

The application returns a JSON response:

```json
{
  "message": "Containerized Web Stack",
  "status": "running"
}
```

The application runs on port `8080`.

## Project Structure

```text
containerized-web-stack/
├── app.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Dockerfile

The Dockerfile defines how the application image is built.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD ["python", "app.py"]
```

### Build Flow

```text
Python Base Image
       ↓
Create /app Working Directory
       ↓
Copy requirements.txt
       ↓
Install Python Dependencies
       ↓
Copy Application Code
       ↓
Create Docker Image
       ↓
Start Container
```

## Build the Image

```bash
docker build -t containerized-web-stack:v1 .
```

After modifying the application, I created a new image version:

```bash
docker build -t containerized-web-stack:v2 .
```

This demonstrated an important Docker concept:

**An image is an immutable application package.**

Changing the source code does not modify an already-built image. A new image must be built.

## Run the Container

```bash
docker run -d \
  --name web-app \
  -p 8080:8080 \
  containerized-web-stack:v2
```

Port mapping:

```text
Mac:8080 → Container:8080 → Flask Application
```

The application inside the container listens on `0.0.0.0:8080`, while Docker publishes container port `8080` to port `8080` on the host.

## Test the Application

```bash
curl http://localhost:8080
```

Example response:

```json
{"message":"Containerized Web Stack","status":"running"}
```

This verifies the complete request path:

```text
curl
  ↓
localhost:8080
  ↓
Docker Port Mapping
  ↓
Container Port 8080
  ↓
Flask Application
  ↓
HTTP Response
```

## Inspect the Running Container

List running containers:

```bash
docker ps
```

Enter the container:

```bash
docker exec -it web-app sh
```

Inside the container I verified:

```bash
pwd
ls -la
python --version
pip show Flask
```

This confirmed that the container has its own filesystem, Python runtime, application files, and installed dependencies.

## Container Logs

Application logs can be inspected with:

```bash
docker logs web-app
```

This is useful when troubleshooting containers because a running container does not necessarily mean that the application is behaving correctly.

## Docker Build Cache

During subsequent builds, Docker reused unchanged build layers:

```text
CACHED
```

For example, changing only `app.py` did not require Flask dependencies to be installed again.

Because `requirements.txt` is copied and installed before `app.py`, Docker can reuse the dependency layer when the dependencies have not changed.

```text
requirements.txt unchanged
        ↓
Dependency layer reused
        ↓
app.py changed
        ↓
Only application layer rebuilt
```

If `requirements.txt` changes, the dependency installation layer must be rebuilt.

## Image Versioning

The project currently uses image tags such as:

```text
containerized-web-stack:v1
containerized-web-stack:v2
```

Tags allow different versions of an application image to coexist.

A container is created from a specific image version. Building `v2` does not automatically update a container that was created from `v1`.

To use the new version, a new container must be created from the new image.

## Useful Commands

```bash
docker images
docker ps
docker ps -a
docker logs web-app
docker exec -it web-app sh
docker stop web-app
docker start web-app
docker rm web-app
```

## Key Concepts Learned

- Docker image vs container
- Dockerfile
- Base images
- Application dependencies
- Image layers
- Docker build cache
- Image tagging and versioning
- Container lifecycle
- Detached mode
- Port publishing
- Container logs
- Container inspection
- Rebuilding images after source-code changes

## Next Steps

The next stages of this project will introduce multiple services and persistent data, including:

- PostgreSQL
- Docker volumes
- Docker networks
- Docker Compose
- Application-to-database communication

The goal is to evolve this single-container application into a complete multi-container web stack.

## Day 7 – PostgreSQL, Docker Networking, Volumes & Compose

Today I extended the project from a single-container Flask application into a multi-container web stack with PostgreSQL.

### What I Built

- Added a PostgreSQL 16 database container
- Connected Flask to PostgreSQL using environment variables
- Used Docker networking for container-to-container communication
- Used Docker DNS with `DB_HOST=db`
- Added a named volume for PostgreSQL persistence
- Migrated the manual `docker run` setup to Docker Compose
- Added a PostgreSQL healthcheck
- Used `depends_on` with `condition: service_healthy`
- Tested container lifecycle and persistent data behavior
- Practiced troubleshooting with YAML, healthcheck, logs, and container state

### Architecture

```text
Client (Mac)
     |
     | localhost:8080
     v
+------------------+
|     web-app      |
|      Flask       |
|      :8080       |
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
|   Docker Volume  |
+------------------+
```

### Docker Networking

The Flask and PostgreSQL containers communicate over the Docker Compose network.

The application connects to PostgreSQL using:

```text
DB_HOST=db
DB_PORT=5432
```

The service name `db` is resolved by Docker's internal DNS, so the application does not need to know the database container's IP address.

The PostgreSQL port does not need to be published to the host because communication between the application and the database happens inside the Docker network.

### Persistent Storage

PostgreSQL stores its data in the named volume:

```text
postgres-data
```

Mounted to:

```text
/var/lib/postgresql/data
```

The database container was deleted and recreated during testing. The `notes` table and its data remained available because the data lifecycle was separated from the container lifecycle.

```text
Container lifecycle != Data lifecycle
```

### Docker Compose

The stack was initially started using separate `docker run` commands.

The complete system is now described in `compose.yaml` and can be started with:

```bash
docker compose up -d
```

Checked with:

```bash
docker compose ps
```

And stopped with:

```bash
docker compose down
```

### Healthcheck

PostgreSQL readiness is checked using:

```text
pg_isready -U appuser -d appdb -p 5432
```

The Flask service waits until PostgreSQL becomes healthy before starting.

```text
Container running != Service healthy
```

A container process can be running while the service inside it is not ready to accept connections.

### Troubleshooting

Several failures were intentionally tested.

#### YAML Syntax Error

A malformed healthcheck definition caused Compose to fail while parsing `compose.yaml`.

The configuration was checked using:

```bash
docker compose config
```

This showed that configuration errors must be fixed before investigating container or application behavior.

#### Unhealthy Database

The PostgreSQL healthcheck was intentionally configured to use port `9999` instead of `5432`.

The database container was running but marked as unhealthy, and the web application did not start because it depended on a healthy database.

The issue was investigated using:

```bash
docker compose ps
docker inspect containerized-web-stack-db-1
docker compose logs db
```

The healthcheck output showed:

```text
/var/run/postgresql:9999 - no response
```

while the PostgreSQL logs showed that the database was correctly listening on port `5432`.

After correcting the healthcheck port, PostgreSQL became healthy and the web application started successfully.

### Verification

The full stack was tested with:

```bash
curl http://localhost:8080
```

The successful response confirmed the complete request flow:

```text
Mac
 ↓
localhost:8080
 ↓
Flask container
 ↓
Docker DNS
 ↓
PostgreSQL container
 ↓
Database response
```

### Key Lessons

- A Dockerfile defines how an image is built.
- Docker Compose defines how multiple containers work together.
- Docker service names can be used as DNS hostnames.
- Environment variables provide runtime configuration.
- Named volumes keep persistent data outside the container lifecycle.
- `docker compose down` removes containers and networks but does not automatically remove external named volumes.
- A running container is not necessarily a healthy service.
- Healthchecks are useful for determining service readiness.
- `depends_on` can be combined with health status to control startup dependencies.
- Troubleshooting should move through configuration, container state, healthcheck, logs, networking, and application behavior.

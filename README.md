# Containerized Web Stack

A hands-on DevOps project focused on building and operating a multi-container web application with Docker.

The current stack includes:

- Flask web application
- PostgreSQL database
- Docker Compose
- Docker networking
- Persistent volumes
- Healthchecks

## Architecture

```text
Client
  |
  | localhost:8080
  v
Flask Web App
  |
  | Docker DNS: db
  v
PostgreSQL
  |
  v
Persistent Docker Volume
```

## Run

Start the stack:

```bash
docker compose up -d
```

Check services:

```bash
docker compose ps
```

Test the application:

```bash
curl http://localhost:8080
```

Stop the stack:

```bash
docker compose down
```

## Current Focus

This project is being developed incrementally to understand how containerized applications, databases, networking, persistent storage, and service orchestration work together.

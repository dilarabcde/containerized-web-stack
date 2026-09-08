# Day 7 - Multi-Container Stack

## Goal

The goal of this lab was to evolve the single-container Flask application from Day 6 into a multi-container application.

The application now consists of two services:

- Flask web application
- PostgreSQL database

During this lab I learned how containers communicate with each other, how database data can survive container deletion, and how Docker Compose can manage multiple services as one application stack.

---

## Architecture

The application architecture evolved from:

```text
Flask Container
```

into:

```text
Mac
 |
 | HTTP :8080
 v
Flask Container
 |
 | PostgreSQL :5432
 v
PostgreSQL Container
 |
 v
Docker Volume
```

The Flask application receives HTTP requests from the host and communicates with PostgreSQL through Docker's internal network.

---

## PostgreSQL Container

A PostgreSQL container was added to the project using the official PostgreSQL image:

```text
postgres:16
```

The database configuration included:

```text
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppassword
POSTGRES_DB=appdb
```

PostgreSQL listens on port:

```text
5432
```

The database port does not need to be published to the Mac because the Flask application communicates with PostgreSQL through Docker's internal network.

---

## Docker Networking

Initially, the Flask and PostgreSQL containers were managed separately.

For two containers to communicate reliably, they must share a Docker network.

The important idea is:

```text
Flask Container
      |
      | Docker Network
      |
      v
PostgreSQL Container
```

Docker provides internal DNS for containers connected to the same user-defined network.

This means the Flask application does not need to know the database container's IP address.

Instead, it can use:

```text
DB_HOST=db
```

Docker resolves:

```text
db
 |
 | Docker DNS
 v
PostgreSQL container IP
```

This is better than hardcoding an IP address because container IP addresses can change when containers are recreated.

---

## Testing Docker DNS

Inside the Flask container, database name resolution was tested with:

```bash
getent hosts db
```

Docker successfully resolved the service name `db` to the PostgreSQL container's IP address.

The important concept is:

```text
Service Name
     |
     v
Docker DNS
     |
     v
Container IP
```

Applications should therefore communicate using service names rather than fixed container IP addresses.

---

## Environment Variables

The Flask application needs information about the database connection.

The following environment variables were provided:

```text
DB_HOST=db
DB_PORT=5432
DB_NAME=appdb
DB_USER=appuser
DB_PASSWORD=apppassword
```

The application reads these values at runtime.

The connection flow is:

```text
Flask
 |
 v
Environment Variables
 |
 v
DB_HOST=db
DB_PORT=5432
 |
 v
Docker DNS
 |
 v
PostgreSQL
```

This avoids hardcoding infrastructure configuration directly into the application source code.

The credentials used in this project are lab-only values and should not be used as production secrets.

---

## Application-to-Database Communication

The Flask application was updated to connect to PostgreSQL.

After the integration, the complete request path became:

```text
curl http://localhost:8080
        |
        v
Mac Port 8080
        |
        v
Docker Port Mapping
        |
        v
Flask Container
        |
        v
Environment Variables
        |
        v
Docker DNS: db
        |
        v
PostgreSQL :5432
        |
        v
SQL Query
        |
        v
Flask JSON Response
```

The application successfully returned a response confirming that PostgreSQL was connected.

---

## Why PostgreSQL Port Is Not Published

The Flask application is accessed from the Mac, so its port is published:

```text
Mac:8080 -> Container:8080
```

PostgreSQL is only accessed by another container.

Therefore:

```text
Flask -> PostgreSQL:5432
```

happens inside the Docker network.

There is no requirement for:

```text
Mac -> PostgreSQL
```

in this architecture.

This means port `5432` does not need to be exposed to the host.

---

## Persistent Data Problem

A database introduces an important problem.

Containers are disposable.

If database files exist only inside the PostgreSQL container, deleting that container can also remove the database data stored in its writable layer.

This was tested by creating a table:

```sql
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    text VARCHAR(100)
);
```

Then a row was inserted:

```sql
INSERT INTO notes (text)
VALUES ('Docker volume test');
```

After deleting and recreating the PostgreSQL container without persistent storage, the table was no longer available.

This demonstrated:

```text
Container deleted
       |
       v
Container filesystem deleted
       |
       v
Database data lost
```

For databases, this is not acceptable.

---

## Docker Volume

A named Docker volume was created:

```bash
docker volume create postgres-data
```

It was mounted to PostgreSQL's data directory:

```text
postgres-data:/var/lib/postgresql/data
```

The architecture became:

```text
PostgreSQL Container
        |
        | mount
        v
postgres-data
Docker Volume
```

Now the database files exist independently from the lifecycle of the PostgreSQL container.

---

## Testing Persistence

A new record was created:

```sql
INSERT INTO notes (text)
VALUES ('This data should survive');
```

The PostgreSQL container was then removed and recreated using the same volume.

After reconnecting to PostgreSQL:

```sql
SELECT * FROM notes;
```

the record was still available.

This demonstrated:

```text
Container A
    |
    v
postgres-data
    |
Container A deleted
    |
    X

postgres-data still exists
    |
    v
Container B
    |
    v
Existing database data
```

The key lesson is:

> Container lifecycle and data lifecycle should be independent.

---

## Docker Compose

Managing the application manually required multiple long Docker commands.

For example, we had to separately define:

- PostgreSQL image
- database environment variables
- Flask image
- port mappings
- database connection variables
- volume mounts
- networking
- startup dependencies

Docker Compose allows this multi-container architecture to be described declaratively in one file:

```text
compose.yaml
```

Instead of manually recreating the architecture with several `docker run` commands, Compose describes the desired application stack.

---

## Compose Services

The Compose configuration contains two services:

```text
services
├── db
└── web-app
```

The `db` service runs PostgreSQL.

The `web-app` service builds and runs the Flask application.

Docker Compose automatically places the services on a shared Compose network.

Therefore the application can use:

```text
DB_HOST=db
```

because `db` is the Compose service name.

---

## Healthcheck

Starting a PostgreSQL container does not necessarily mean PostgreSQL is immediately ready to accept connections.

There is an important difference:

```text
Container started
       ≠
Database ready
```

A PostgreSQL healthcheck was added using:

```bash
pg_isready -U appuser -d appdb -p 5432
```

The healthcheck allows Docker to determine whether PostgreSQL is actually ready to accept database connections.

---

## depends_on

The Flask service depends on PostgreSQL.

The Compose configuration uses:

```yaml
depends_on:
  db:
    condition: service_healthy
```

The startup relationship becomes:

```text
Start PostgreSQL Container
          |
          v
Run Healthcheck
          |
          v
PostgreSQL Healthy
          |
          v
Start Flask Container
```

This is more reliable than starting both containers without checking database readiness.

---

## Docker Compose Lifecycle

The entire application stack can be started using:

```bash
docker compose up -d
```

The status of the services can be inspected using:

```bash
docker compose ps
```

The stack can be stopped and removed using:

```bash
docker compose down
```

The important difference from the previous approach is:

```text
Before:

docker run db ...
docker run web-app ...
network configuration...
environment variables...
volume configuration...
```

With Compose:

```text
compose.yaml
      |
      v
docker compose up -d
      |
      v
Complete Application Stack
```

---

## External Volume

The project already had a named volume called:

```text
postgres-data
```

The Compose configuration reused this existing volume.

Therefore it was declared as:

```yaml
volumes:
  postgres-data:
    external: true
```

This tells Docker Compose:

```text
Do not create this volume.
Use the existing postgres-data volume.
```

Because the volume exists independently from the Compose stack:

```bash
docker compose down
```

can remove the application containers and Compose network while the database data remains stored in the external volume.

---

## Final Architecture

At the end of Day 7, the application architecture was:

```text
                 Mac
                  |
                  | localhost:8080
                  v
        +-------------------+
        |   Flask Web App   |
        |       :8080       |
        +-------------------+
                  |
                  | DB_HOST=db
                  | DB_PORT=5432
                  v
           Docker Network
                  |
                  | Docker DNS
                  v
        +-------------------+
        |    PostgreSQL     |
        |       :5432       |
        +-------------------+
                  |
                  | mount
                  v
        +-------------------+
        |   postgres-data   |
        |   Docker Volume   |
        +-------------------+
```

There are now three different concerns:

```text
Application
    |
    +-- Flask Container

Database
    |
    +-- PostgreSQL Container

Persistent Storage
    |
    +-- Docker Volume
```

Docker Compose manages how these components work together.

---

## Troubleshooting Lessons

Several failures during the lab helped demonstrate how the architecture works.

### Containers on Different Networks

If Flask and PostgreSQL are not connected to the same Docker network, Flask cannot reliably reach the database using the service name.

### Wrong DNS Command

The correct command was:

```bash
getent hosts db
```

not:

```bash
getent host db
```

### Container Running vs Service Ready

A PostgreSQL container can be running while the database is not yet ready.

This is why the healthcheck was introduced.

### Wrong Healthcheck Port

A healthcheck using the wrong port caused PostgreSQL to be marked as:

```text
unhealthy
```

even though PostgreSQL itself was running correctly.

Inspecting the health status and PostgreSQL logs showed that PostgreSQL was actually listening on:

```text
5432
```

This demonstrated an important troubleshooting principle:

> An unhealthy status does not automatically mean the application itself is broken. The healthcheck configuration can also be wrong.

---

## Useful Commands

```bash
docker compose up -d

docker compose ps

docker compose down

docker compose logs

docker compose logs db

docker volume ls

docker inspect <container>

docker exec -it <container> sh

curl http://localhost:8080
```

---

## Key Concepts Learned

During this lab I learned:

- Multi-container application architecture
- PostgreSQL containers
- Container-to-container communication
- Docker networks
- Docker DNS
- Service-name based communication
- Environment variables
- Application-to-database connections
- Host ports vs container ports
- Persistent database storage
- Docker named volumes
- Container lifecycle vs data lifecycle
- Docker Compose
- Compose services
- Compose networking
- Healthchecks
- `depends_on`
- Service readiness
- External Docker volumes
- Multi-container troubleshooting

---

## Mental Model

The most important mental model from Day 7 is:

```text
User Request
     |
     v
Host Port
     |
     v
Web Container
     |
     v
Docker Network
     |
     v
Docker DNS
     |
     v
Database Container
     |
     v
Persistent Volume
```

Day 6 answered:

```text
How do I package and run one application?
```

Day 7 answered:

```text
How do multiple containers communicate,
persist data, and operate as one stack?
```

Dockerfile defines how an individual application image is built.

Docker Compose defines how multiple services work together.

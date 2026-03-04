# Home Lab Infrastructure Basics

This document describes the core architecture and operational principles of the `home_lab` project.  
It serves as a reference so the infrastructure can be easily resumed, maintained, or expanded in the future.

---

## Architecture Overview

### Server

- **OS:** Ubuntu  
- **Container Runtime:** Docker + Docker Compose v2  
- **Server IP:** `10.18.18.11`  
- **Domain:** Managed via Cloudflare  
- **Access:** Currently limited to the local network (LAN)

---

## Networking Model

The infrastructure uses a single internal Docker network.

**Design principles:**
- One shared Docker network: `home_lab`
- Databases are **not exposed publicly**
- Web services are exposed through **Nginx Proxy Manager**

**Root compose network definition (example):**
```yaml
networks:
  home_lab:
    name: home_lab
    driver: bridge
```

**Each service joins the network:**
```yaml
networks:
  - home_lab
```

Avoid using `external: true` unless absolutely necessary. The root compose file should manage network creation.

---

## Project Structure

Repository layout:
```text
home_lab/
  docker-compose.yml
  .env

  infra/
    npm/
    portainer/
    uptime/
    services/
      postgres/
      plex/
      pihole/

  code/
    web_app/
```

**Structure principles:**
- One service = one docker compose file
- Avoid monolithic compose files
- Infrastructure should be separated from application code

---

## Secrets Management

The current implementation uses a single `.env` file at the project root. This is acceptable for a home lab environment.

**Security rules:**
- `.env` must **not** be committed to Git
- Recommended permissions:
```bash
chmod 600 .env
```
- Secrets should never be hardcoded in compose files.

**Example `.env`:**
```env
PG_DEFAULT_DB=lab
PG_DEFAULT_USER=lab_admin
PG_DEFAULT_PASSWORD=very_strong_password
```

**Future improvements may include:**
- Docker Secrets
- Password files (`*_FILE`)
- HashiCorp Vault
- Bitwarden secret integration

---

## Database Standard (PostgreSQL)

PostgreSQL is used as the primary database platform for services.

**Reasons:**
- Widely supported by modern frameworks
- Highly stable and production-ready
- Strong ecosystem

**Operational rules:**
- Run one PostgreSQL container
- Each application has its own database
- Each application has its own database user
- Database ports should not be publicly exposed

**Internal connection example:**
```text
postgresql://user:password@postgres:5432/database
```

`postgres` refers to the Docker service hostname.

---

## Portainer Usage Model

Portainer should be used as:
- a monitoring interface
- a visual management UI
- a debugging tool

Portainer should **not** be the source of truth for infrastructure configuration.

**Source of truth:** the Git repository.

**Deployment (CLI):**
```bash
git pull
docker compose up -d
```

**Future option:** GitOps deployment through Portainer where each service is deployed directly from Git.

---

## Deployment Workflow

Standard workflow when making infrastructure changes:

1. Modify compose files locally  
2. Commit changes to the repository  
3. Update the server:
```bash
git pull
docker compose up -d
```

**Important rule:** Do not manually modify running containers. All changes must originate from source configuration.

---

## Basic Security Practices

Minimum security practices:
- Do not expose databases externally
- Avoid binding services to `0.0.0.0` unless necessary
- Use strong passwords
- Regularly clean unused Docker resources

Useful commands:
```bash
docker ps
docker image prune
docker volume ls
```

External access should remain blocked by the router firewall unless explicitly required.

---

## Future Infrastructure Evolution

The infrastructure can evolve gradually.

### Network Segmentation (later)

Introduce separate networks:
```text
frontend
backend
```

- Web services connect to `frontend`
- Databases and internal services connect to `backend`

### Secrets Management Improvements (later)

- Docker secrets
- External secret management

### GitOps Deployment (later)

Deploy stacks directly from Git via Portainer. Each service becomes an independent stack.

### Observability Stack (later)

- Prometheus
- Grafana
- Loki (optional)

---

## Core Principles

1. Simplicity over complexity  
2. Git is the source of truth  
3. Each service should be isolated  
4. Databases should remain internal  
5. Avoid unnecessary infrastructure complexity  

---

## Summary

The home lab infrastructure is designed to be:
- simple
- reproducible
- scalable

This foundation allows new services and applications to be added without restructuring the entire environment.

---

## Documentation script:

### Requirements

Install Python:
`sudo apt install python3-pip`

and 

`pip3 install pyyaml`

There is no package for Ubuntu, so use this.
`sudo apt install python3-yaml`

`sqlite3` is a part of Python, nothing extra is required.

From the repository root:
`python3 scripts/generate-services-md.py`

Generates:

`docs/services.md`

If your NPM is elswhere:

`python3 scripts/generate-services-md.py --npm-db infra/npm/data/database.sqlite`

If Mermaid in not wanted:

`python3 scripts/generate-services-md.py --no-mermaid`
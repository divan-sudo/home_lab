# Services Inventory

_Auto-generated from `docker compose config` on **2026-03-04 21:55 UTC**._

This file is generated. Do not edit manually.

## Summary

- Total services: **7**
- NPM DB: `/home/divan/home_lab/infra/npm/data/database.sqlite`

## Services

| Service | Image | Ports | Networks | Volumes |
|---|---|---|---|---|
| `adminer` | `adminer:latest` | `${SERVER_IP}:8081:8080` | `home_lab` | `` |
| `lab-web` | `nginx:alpine` | `` | `home_lab` | `bind:/home/divan/home_lab/code/web_app/web:/usr/share/nginx/html:ro` |
| `npm` | `jc21/nginx-proxy-manager:latest` | `80:80/tcp (ingress), 81:81/tcp (ingress), 443:443/tcp (ingress)` | `home_lab` | `bind:/home/divan/home_lab/infra/npm/data:/data, bind:/home/divan/home_lab/infra/npm/letsencrypt:/etc/letsencrypt` |
| `plex` | `lscr.io/linuxserver/plex:latest` | `` | `` | `bind:/opt/plex/config:/config, bind:/mnt/nas:/movies` |
| `portainer` | `portainer/portainer-ce:latest` | `` | `home_lab` | `bind:/var/run/docker.sock:/var/run/docker.sock, volume:portainer_data:/data` |
| `postgres` | `postgres:16` | `${SERVER_IP}:5432:5432` | `home_lab` | `volume:pg_data:/var/lib/postgresql/data` |
| `uptime-kuma` | `louislam/uptime-kuma:1` | `` | `home_lab` | `volume:uptime_data:/app/data` |

## Reverse Proxy Hosts (Nginx Proxy Manager)

_Failed to read NPM database: `OperationalError: no such table: proxy_hosts`_

## Topology

High-level traffic flow:

- Client → DNS → `10.18.18.11` → Nginx Proxy Manager → Service container

### Diagram (Mermaid)

```mermaid
flowchart LR
  C[Client] --> D[DNS]
  D --> S[10.18.18.11]
  S --> NPM[Nginx Proxy Manager]
  NPM --> SVCS[Service containers]
```

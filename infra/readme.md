# Home Lab Networking and Service Access

This document describes how services in the `home_lab` infrastructure
are accessed through the internal network using **Nginx Proxy Manager
(NPM)** and how DNS resolution will be handled using **Pi-hole**.

The goal is to provide clean service URLs, centralized routing, and TLS
support.

------------------------------------------------------------------------

# Architecture Overview

The home lab environment runs on a single server with Docker.

Server details:

-   OS: Ubuntu
-   Container runtime: Docker + Docker Compose
-   Server IP: `10.18.18.11`
-   Domain: `divan-sudo.com`
-   Reverse proxy: Nginx Proxy Manager
-   Future DNS server: Pi-hole

All services are routed through **Nginx Proxy Manager**.

    Client
       │
       ▼
    DNS (Cloudflare or Pi-hole)
       │
       ▼
    Nginx Proxy Manager
       │
       ├── dashboard.lab.divan-sudo.com → lab-web:80
       ├── portainer.lab.divan-sudo.com → portainer:9000
       └── uptime.lab.divan-sudo.com → uptime-kuma:3001

------------------------------------------------------------------------

# Current Access Model

Services are exposed using subdomains under:

    *.lab.divan-sudo.com

Example services:

  Service       Domain                         Destination
  ------------- ------------------------------ ------------------
  Dashboard     dashboard.lab.divan-sudo.com   lab-web:80
  Portainer     portainer.lab.divan-sudo.com   portainer:9000
  Uptime Kuma   uptime.lab.divan-sudo.com      uptime-kuma:3001

Requests flow as follows:

    Browser
       │
       ▼
    Cloudflare DNS
       │
       ▼
    10.18.18.11
       │
       ▼
    Nginx Proxy Manager
       │
       ▼
    Docker service

TLS certificates are issued by **Let's Encrypt** via Nginx Proxy
Manager.

------------------------------------------------------------------------

# Docker Networking

All services run inside the shared Docker network:

    home_lab

Example network definition:

``` yaml
networks:
  home_lab:
    name: home_lab
    driver: bridge
```

Each service joins this network:

``` yaml
networks:
  - home_lab
```

Services communicate internally using Docker service names:

    portainer:9000
    uptime-kuma:3001
    lab-web:80

------------------------------------------------------------------------

# Internal Domains (Future Setup)

When Pi-hole is deployed, the lab will support **internal DNS domains**.

Example internal domains:

    portainer.lab
    uptime.lab
    dashboard.lab
    plex.lab

These domains will resolve locally through Pi-hole.

Example DNS mapping:

    portainer.lab → 10.18.18.11
    uptime.lab → 10.18.18.11
    dashboard.lab → 10.18.18.11

All traffic still routes through Nginx Proxy Manager.

Flow with internal DNS:

    Client
       │
       ▼
    Pi-hole DNS
       │
       ▼
    10.18.18.11
       │
       ▼
    Nginx Proxy Manager
       │
       ▼
    Service container

------------------------------------------------------------------------

# Wildcard DNS (Optional)

Pi-hole can provide wildcard DNS resolution.

Example configuration:

    *.lab → 10.18.18.11

This allows automatic resolution for new services without adding DNS
entries.

Example working URLs:

    grafana.lab
    portainer.lab
    uptime.lab
    plex.lab

Only Nginx Proxy Manager configuration is required for new services.

------------------------------------------------------------------------

# SSL Considerations

Let's Encrypt cannot issue certificates for non-public domains such as:

    *.lab

Available options:

### Option 1 --- Self-signed certificates

Simplest option for internal services.

### Option 2 --- Use existing public wildcard certificate

Example:

    *.lab.divan-sudo.com

Issued through Cloudflare and used by Nginx Proxy Manager.

------------------------------------------------------------------------

# Best Practices

Recommended practices for the home lab networking setup.

### Use reverse proxy for all services

Avoid accessing services via ports such as:

    http://10.18.18.11:3001

Use domain-based access instead:

    https://uptime.lab.divan-sudo.com

### Keep runtime data outside Git

Do not commit runtime directories such as:

    infra/npm/data
    infra/npm/letsencrypt

Example `.gitignore`:

    infra/npm/data/*
    infra/npm/letsencrypt/*

### Use Docker service names internally

Containers should communicate via:

    http://service-name:port

Example:

    http://portainer:9000
    http://uptime-kuma:3001

------------------------------------------------------------------------

# Future Improvements

Planned infrastructure improvements include:

-   Deploy Pi-hole as the internal DNS server
-   Introduce internal domains (`*.lab`)
-   Implement monitoring stack (Grafana + Prometheus)
-   Automate container updates
-   Add backup strategy for Docker volumes

------------------------------------------------------------------------

# Summary

The home lab networking model provides:

-   centralized routing through Nginx Proxy Manager
-   TLS-enabled service access
-   clean service URLs
-   container-to-container networking
-   future support for internal DNS via Pi-hole

This architecture ensures a scalable and maintainable infrastructure for
adding new services.

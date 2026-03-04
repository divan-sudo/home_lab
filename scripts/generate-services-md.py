#!/usr/bin/env python3
"""
Generate docs/services.md from:
- `docker compose config --no-interpolate` (merged config; supports `include:`)
- Nginx Proxy Manager SQLite database (optional) to inventory proxy hosts

Output sections:
- Services Inventory (image/ports/networks/volumes)
- NPM Proxy Hosts Inventory (domain -> upstream, SSL flags)
- Topology summary + Mermaid diagram (optional)

Usage:
  python3 scripts/generate-services-md.py

Optional:
  python3 scripts/generate-services-md.py --npm-db infra/npm/data/database.sqlite
  python3 scripts/generate-services-md.py --output docs/services.md --no-mermaid
"""

from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ----------------------------
# Compose parsing helpers
# ----------------------------

def run_compose_config() -> str:
    cmd = ["docker", "compose", "config", "--no-interpolate"]
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print("ERROR: failed to run `docker compose config`.\n")
        print(e.output)
        sys.exit(1)


def normalize_ports(ports: Any) -> str:
    if not ports:
        return ""
    items: List[str] = []
    for p in ports:
        if isinstance(p, str):
            items.append(p)
        elif isinstance(p, dict):
            target = p.get("target")
            published = p.get("published")
            proto = p.get("protocol", "tcp")
            mode = p.get("mode")
            if published and target:
                s = f"{published}:{target}/{proto}"
            elif target:
                s = f"{target}/{proto}"
            else:
                s = str(p)
            if mode:
                s += f" ({mode})"
            items.append(s)
        else:
            items.append(str(p))
    return ", ".join(items)


def normalize_networks(networks: Any) -> str:
    if not networks:
        return ""
    if isinstance(networks, list):
        return ", ".join(str(x) for x in networks)
    if isinstance(networks, dict):
        return ", ".join(networks.keys())
    return str(networks)


def normalize_volumes(volumes: Any) -> str:
    if not volumes:
        return ""
    items: List[str] = []
    for v in volumes:
        if isinstance(v, str):
            items.append(v)
        elif isinstance(v, dict):
            src = v.get("source", "")
            tgt = v.get("target", "")
            ro = v.get("read_only", False)
            typ = v.get("type", "")
            s = f"{src}:{tgt}"
            if ro:
                s += ":ro"
            if typ:
                s = f"{typ}:{s}"
            items.append(s)
        else:
            items.append(str(v))
    return ", ".join(items)


def labels_to_dict(labels: Any) -> Dict[str, str]:
    if not labels:
        return {}
    if isinstance(labels, dict):
        return {str(k): str(v) for k, v in labels.items()}
    if isinstance(labels, list):
        out: Dict[str, str] = {}
        for item in labels:
            if isinstance(item, str) and "=" in item:
                k, v = item.split("=", 1)
                out[k.strip()] = v.strip()
        return out
    return {}


def esc_md(s: str) -> str:
    return (s or "").replace("|", "\\|").strip()


# ----------------------------
# NPM DB parsing
# ----------------------------

@dataclass
class NpmHost:
    id: int
    domain_names: str
    forward_host: str
    forward_port: int
    enabled: bool
    ssl_forced: bool
    certificate_id: Optional[int]


def guess_npm_db_path(repo_root: Path) -> Optional[Path]:
    """
    Try common paths for NPM sqlite DB within repo checkout.
    Adjust if your NPM data dir differs.
    """
    candidates = [
        repo_root / "infra" / "npm" / "data" / "database.sqlite",
        repo_root / "infra" / "npm" / "data" / "npm.sqlite",
        repo_root / "infra" / "npm" / "data" / "data.sqlite",
        # Some setups mount /data directly and DB ends up here:
        repo_root / "infra" / "npm" / "database.sqlite",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def read_npm_hosts(db_path: Path) -> List[NpmHost]:
    """
    Reads Nginx Proxy Manager proxy_hosts from sqlite.
    Schema is stable across many NPM versions; if it changes, we fail gracefully.
    """
    hosts: List[NpmHost] = []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()

        # Table: proxy_hosts
        # Columns used:
        # - id, domain_names, forward_host, forward_port, enabled, ssl_forced, certificate_id
        cur.execute(
            """
            SELECT id, domain_names, forward_host, forward_port, enabled, ssl_forced, certificate_id
            FROM proxy_hosts
            ORDER BY id ASC;
            """
        )
        rows = cur.fetchall()
        for r in rows:
            hosts.append(
                NpmHost(
                    id=int(r["id"]),
                    domain_names=str(r["domain_names"] or ""),
                    forward_host=str(r["forward_host"] or ""),
                    forward_port=int(r["forward_port"] or 0),
                    enabled=bool(r["enabled"]),
                    ssl_forced=bool(r["ssl_forced"]),
                    certificate_id=(int(r["certificate_id"]) if r["certificate_id"] is not None else None),
                )
            )
    finally:
        conn.close()
    return hosts


def parse_domain_list(domain_names: str) -> List[str]:
    # NPM stores domain_names as comma-separated string
    parts = [d.strip() for d in (domain_names or "").split(",")]
    return [p for p in parts if p]


# ----------------------------
# Rendering
# ----------------------------

def render_services_table(services: Dict[str, Any]) -> List[str]:
    rows = sorted(services.items(), key=lambda x: x[0])

    lines: List[str] = []
    lines.append("## Services")
    lines.append("")
    lines.append("| Service | Image | Ports | Networks | Volumes |")
    lines.append("|---|---|---|---|---|")

    for name, svc in rows:
        image = str(svc.get("image") or "")
        ports = normalize_ports(svc.get("ports"))
        nets = normalize_networks(svc.get("networks"))
        vols = normalize_volumes(svc.get("volumes"))

        lines.append(
            f"| `{esc_md(name)}` | `{esc_md(image)}` | `{esc_md(ports)}` | `{esc_md(nets)}` | `{esc_md(vols)}` |"
        )

    lines.append("")
    return lines


def render_npm_hosts(hosts: List[NpmHost]) -> List[str]:
    lines: List[str] = []
    lines.append("## Reverse Proxy Hosts (Nginx Proxy Manager)")
    lines.append("")
    if not hosts:
        lines.append("_No proxy hosts found in the NPM database._")
        lines.append("")
        return lines

    lines.append("| Domains | Upstream | Enabled | Force SSL | Cert ID |")
    lines.append("|---|---|---:|---:|---:|")

    # Expand domains so it's readable even with multiple domains per host
    for h in hosts:
        domains = ", ".join(parse_domain_list(h.domain_names))
        upstream = f"{h.forward_host}:{h.forward_port}"
        lines.append(
            f"| `{esc_md(domains)}` | `{esc_md(upstream)}` | `{str(h.enabled)}` | `{str(h.ssl_forced)}` | `{'' if h.certificate_id is None else h.certificate_id}` |"
        )

    lines.append("")
    lines.append("> Note: NPM host routing is stored in the NPM database, not in docker compose.")
    lines.append("")
    return lines


def render_topology(hosts: List[NpmHost], show_mermaid: bool) -> List[str]:
    lines: List[str] = []
    lines.append("## Topology")
    lines.append("")
    lines.append("High-level traffic flow:")
    lines.append("")
    lines.append("- Client → DNS → `10.18.18.11` → Nginx Proxy Manager → Service container")
    lines.append("")

    if hosts:
        lines.append("### Routes")
        lines.append("")
        for h in hosts:
            upstream = f"{h.forward_host}:{h.forward_port}"
            for d in parse_domain_list(h.domain_names):
                lines.append(f"- `{d}` → `{upstream}`")
        lines.append("")

    if show_mermaid:
        lines.append("### Diagram (Mermaid)")
        lines.append("")
        lines.append("```mermaid")
        lines.append("flowchart LR")
        lines.append('  C[Client] --> D[DNS]')
        lines.append('  D --> S[10.18.18.11]')
        lines.append('  S --> NPM[Nginx Proxy Manager]')
        if hosts:
            # dedupe upstream nodes
            upstreams = {}
            for h in hosts:
                key = f"{h.forward_host}:{h.forward_port}"
                upstreams[key] = h
            i = 1
            node_map: Dict[str, str] = {}
            for up in upstreams.keys():
                node = f"U{i}"
                node_map[up] = node
                lines.append(f'  NPM --> {node}["{up}"]')
                i += 1
        else:
            lines.append('  NPM --> SVCS[Service containers]')
        lines.append("```")
        lines.append("")

    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="docs/services.md", help="Output markdown file path")
    ap.add_argument("--npm-db", default="", help="Path to NPM sqlite DB (optional). If omitted, auto-detect is attempted.")
    ap.add_argument("--no-mermaid", action="store_true", help="Disable Mermaid diagram output")
    args = ap.parse_args()

    repo_root = Path.cwd()
    out_path = repo_root / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)

    merged_yaml = run_compose_config()
    cfg = yaml.safe_load(merged_yaml) or {}
    services: Dict[str, Any] = cfg.get("services") or {}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # NPM DB
    npm_db_path: Optional[Path] = Path(args.npm_db).resolve() if args.npm_db else guess_npm_db_path(repo_root)
    npm_hosts: List[NpmHost] = []
    npm_error: Optional[str] = None

    if npm_db_path and npm_db_path.exists():
        try:
            npm_hosts = read_npm_hosts(npm_db_path)
        except Exception as e:
            npm_error = f"{type(e).__name__}: {e}"
    else:
        npm_db_path = None  # for clean rendering

    lines: List[str] = []
    lines.append("# Services Inventory")
    lines.append("")
    lines.append(f"_Auto-generated from `docker compose config` on **{now}**._")
    lines.append("")
    lines.append("This file is generated. Do not edit manually.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total services: **{len(services)}**")
    if npm_db_path:
        lines.append(f"- NPM DB: `{npm_db_path}`")
    else:
        lines.append("- NPM DB: _not found (skipping NPM host inventory)_")
    lines.append("")

    lines.extend(render_services_table(services))

    if npm_error:
        lines.append("## Reverse Proxy Hosts (Nginx Proxy Manager)")
        lines.append("")
        lines.append(f"_Failed to read NPM database: `{npm_error}`_")
        lines.append("")
    else:
        lines.extend(render_npm_hosts(npm_hosts))

    lines.extend(render_topology(npm_hosts, show_mermaid=not args.no_mermaid))

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
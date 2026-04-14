#!/usr/bin/env python3
"""Startup-Skript: Cloudflare IPs zu HA trusted_proxies hinzufügen."""
import sys
import os

sys.path.insert(0, "/app")
import ha_config

try:
    merged = ha_config.update_trusted_proxies(include_ipv6=True)
    print(f"trusted_proxies aktualisiert: {len(merged)} Einträge")
except Exception as e:
    print(f"Fehler beim Aktualisieren der trusted_proxies: {e}", file=sys.stderr)
    sys.exit(1)

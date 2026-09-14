# Cloudflare Route Manager – Home Assistant Add-on

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/gregorwolf1973)

Dieses Add-on ermöglicht die Verwaltung von Cloudflare DNS-Einträgen und Tunnel-Routen
direkt aus Home Assistant heraus.

## Features

- **DNS-Verwaltung** – Einträge anzeigen, erstellen, bearbeiten und löschen (A, AAAA, CNAME, MX, TXT, SRV)
- **Tunnel-Routen** – Cloudflare Tunnel Routen konfigurieren (Hostname → Service)
- **Trusted Proxies** – Cloudflare IP-Bereiche automatisch in `configuration.yaml` eintragen
- **NPM-Hilfe** – Nginx Proxy Manager Konfiguration und Nginx-Snippets generieren

## Installation

1. Addon-Repository in Home Assistant hinzufügen:
   ```
   https://github.com/gregorwolf1973/cloudflare-routes-addon
   ```
2. Add-on installieren
3. Konfiguration befüllen (API-Token, Zone-ID, Account-ID)
4. Add-on starten → öffnet sich in der Sidebar

## Konfiguration

| Option | Beschreibung |
|--------|-------------|
| `cloudflare_api_token` | Cloudflare API-Token (empfohlen, Berechtigung: DNS:Edit, Zone:Read) |
| `cloudflare_email` | E-Mail für Global API Key Authentifizierung (alternativ) |
| `cloudflare_global_api_key` | Global API Key (alternativ zum API-Token) |
| `zone_id` | Zone-ID der Domain (Cloudflare Dashboard → Zone Overview → rechte Spalte) |
| `account_id` | Account-ID (für Tunnel-Verwaltung, Cloudflare Dashboard → rechte Spalte) |
| `domain` | Deine Domain (z.B. `example.com`) |
| `update_trusted_proxies` | Beim Start Cloudflare IPs automatisch in `configuration.yaml` eintragen |
| `log_level` | Log-Level: `info`, `debug`, `warning`, etc. |

## API-Token Berechtigungen

Minimal-Berechtigungen für das API-Token:
- **Zone / DNS / Edit** – DNS-Einträge verwalten
- **Zone / Zone / Read** – Zone-Informationen lesen
- **Account / Cloudflare Tunnel / Edit** – Tunnel-Routen verwalten (optional)

## Hinweise

- Das Add-on schreibt in `/config/configuration.yaml`. Ein Backup empfiehlt sich.
- Für die Tunnel-Verwaltung muss eine `account_id` angegeben sein.
- Tunnel müssen im [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com) angelegt worden sein.

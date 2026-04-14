# Changelog

## 1.0.1
- Fix: `!include`-Tags in `configuration.yaml` führten nicht mehr zum Absturz (Custom YAML-Loader)
- Fix: Dashboard-500-Fehler wenn trusted_proxies nicht gelesen werden konnten
- Fix: trusted_proxies-Update schreibt nun text-basiert und zerstört keine `!include`-Direktiven
- Bei `http: !include …` erscheint eine klare Fehlermeldung statt eines Absturzes

## 1.0.0
- Erstveröffentlichung
- DNS-Einträge anzeigen, erstellen und löschen (A, AAAA, CNAME, MX, TXT, SRV)
- Cloudflare Tunnel-Routen verwalten (Hinzufügen / Entfernen)
- Automatisches Eintragen der Cloudflare IPv4 und IPv6 IP-Bereiche als `trusted_proxies`
- NPM (Nginx Proxy Manager) Konfigurationshilfe mit Nginx-Snippet-Generator
- Unterstützt API-Token und Global API Key Authentifizierung
- Ingress-Integration für Home Assistant Sidebar

import json
import logging
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

import ha_config
from cloudflare_api import CloudflareAPI


class IngressFix:
    """Setzt SCRIPT_NAME aus dem X-Ingress-Path Header den HA schickt,
    damit url_for() korrekte absolute Pfade erzeugt."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        ingress_path = environ.get("HTTP_X_INGRESS_PATH", "").rstrip("/")
        if ingress_path:
            environ["SCRIPT_NAME"] = ingress_path
        return self.app(environ, start_response)


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.wsgi_app = IngressFix(ProxyFix(app.wsgi_app, x_for=1, x_proto=1))

OPTIONS_FILE = "/data/options.json"
PORT = int(os.environ.get("INGRESS_PORT", 8200))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_options():
    try:
        with open(OPTIONS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def get_cf():
    return CloudflareAPI(get_options())


def is_configured():
    opts = get_options()
    has_token = bool(opts.get("cloudflare_api_token") or opts.get("cloudflare_global_api_key"))
    has_zone = bool(opts.get("zone_id"))
    return has_token and has_zone


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if not is_configured():
        return render_template("not_configured.html")

    cf = get_cf()
    stats = {"dns_count": 0, "tunnel_count": 0, "zone_name": "", "connected": False}
    error = None

    try:
        zone = cf.get_zone_info()
        stats["zone_name"] = zone.get("name", "")
        stats["connected"] = True
        dns = cf.list_dns_records()
        stats["dns_count"] = len(dns)
        tunnels = cf.list_tunnels()
        stats["tunnel_count"] = len(tunnels)
    except Exception as e:
        error = str(e)
        log.error("Dashboard-Fehler: %s", e)

    try:
        present, missing = ha_config.cf_ips_in_config()
        cf_present, cf_missing = len(present), len(missing)
    except Exception as e:
        log.warning("Proxy-Status konnte nicht gelesen werden: %s", e)
        cf_present, cf_missing = 0, 0

    return render_template(
        "index.html",
        stats=stats,
        error=error,
        cf_present=cf_present,
        cf_missing=cf_missing,
        options=get_options(),
    )


# ── DNS-Einträge ─────────────────────────────────────────────────────────────

@app.route("/dns")
def dns_records():
    cf = get_cf()
    records, error = [], None
    try:
        records = cf.list_dns_records()
    except Exception as e:
        error = str(e)
    return render_template("dns.html", records=records, error=error)


@app.route("/dns/create", methods=["POST"])
def create_dns():
    cf = get_cf()
    try:
        rtype = request.form["type"]
        name = request.form["name"].strip()
        content = request.form["content"].strip()
        ttl = int(request.form.get("ttl", 1))
        proxied = request.form.get("proxied") == "true"
        cf.create_dns_record(rtype, name, content, ttl, proxied)
        flash(f"DNS-Eintrag \"{name}\" wurde erstellt.", "success")
    except Exception as e:
        flash(f"Fehler beim Erstellen: {e}", "danger")
    return redirect(url_for("dns_records"))


@app.route("/dns/delete/<record_id>", methods=["POST"])
def delete_dns(record_id):
    cf = get_cf()
    try:
        cf.delete_dns_record(record_id)
        flash("DNS-Eintrag wurde gelöscht.", "success")
    except Exception as e:
        flash(f"Fehler beim Löschen: {e}", "danger")
    return redirect(url_for("dns_records"))


# ── Tunnel-Routen ─────────────────────────────────────────────────────────────

@app.route("/tunnels")
def tunnels():
    cf = get_cf()
    tunnels_list, tunnel_configs, error = [], {}, None
    try:
        tunnels_list = cf.list_tunnels()
        for t in tunnels_list:
            try:
                tunnel_configs[t["id"]] = cf.get_tunnel_config(t["id"])
            except Exception:
                tunnel_configs[t["id"]] = {}
    except Exception as e:
        error = str(e)
    return render_template(
        "tunnels.html", tunnels=tunnels_list, tunnel_configs=tunnel_configs, error=error
    )


@app.route("/tunnels/<tunnel_id>/routes/add", methods=["POST"])
def add_tunnel_route(tunnel_id):
    cf = get_cf()
    try:
        hostname = request.form["hostname"].strip()
        service = request.form["service"].strip()

        current = cf.get_tunnel_config(tunnel_id)
        ingress = current.get("config", {}).get("ingress", [])
        ingress = [r for r in ingress if r.get("hostname")]
        ingress.append({"hostname": hostname, "service": service})
        ingress.append({"service": "http_status:404"})

        cf.update_tunnel_config(tunnel_id, {"config": {"ingress": ingress}})
        flash(f"Route \"{hostname} → {service}\" wurde hinzugefügt.", "success")
    except Exception as e:
        flash(f"Fehler: {e}", "danger")
    return redirect(url_for("tunnels"))


@app.route("/tunnels/<tunnel_id>/routes/delete", methods=["POST"])
def delete_tunnel_route(tunnel_id):
    cf = get_cf()
    try:
        hostname = request.form["hostname"]
        current = cf.get_tunnel_config(tunnel_id)
        ingress = current.get("config", {}).get("ingress", [])
        ingress = [r for r in ingress if r.get("hostname") != hostname]
        cf.update_tunnel_config(tunnel_id, {"config": {"ingress": ingress}})
        flash(f"Route \"{hostname}\" wurde entfernt.", "success")
    except Exception as e:
        flash(f"Fehler: {e}", "danger")
    return redirect(url_for("tunnels"))


# ── Trusted Proxies ───────────────────────────────────────────────────────────

@app.route("/proxies")
def proxies():
    present, missing = ha_config.cf_ips_in_config()
    other = [
        ip for ip in ha_config.get_current_trusted_proxies()
        if ip not in ha_config.CLOUDFLARE_IPV4 + ha_config.CLOUDFLARE_IPV6
    ]
    return render_template(
        "proxies.html",
        cf_ipv4=ha_config.CLOUDFLARE_IPV4,
        cf_ipv6=ha_config.CLOUDFLARE_IPV6,
        present=present,
        missing=missing,
        other=other,
    )


@app.route("/proxies/update", methods=["POST"])
def update_proxies():
    try:
        include_ipv6 = request.form.get("include_ipv6", "true") == "true"
        merged = ha_config.update_trusted_proxies(include_ipv6)
        flash(f"trusted_proxies aktualisiert – {len(merged)} Einträge gesamt.", "success")
    except Exception as e:
        flash(f"Fehler: {e}", "danger")
    return redirect(url_for("proxies"))


@app.route("/proxies/remove", methods=["POST"])
def remove_proxies():
    try:
        remaining = ha_config.remove_cf_trusted_proxies()
        flash(f"Cloudflare IPs entfernt. Verbleibend: {len(remaining)} Einträge.", "warning")
    except Exception as e:
        flash(f"Fehler: {e}", "danger")
    return redirect(url_for("proxies"))


# ── NPM-Hilfe ─────────────────────────────────────────────────────────────────

@app.route("/npm")
def npm_helper():
    domain = get_options().get("domain", "")
    return render_template("npm_helper.html", domain=domain, config=None, form_data={})


@app.route("/npm/generate", methods=["POST"])
def npm_generate():
    hostname = request.form.get("hostname", "").strip()
    internal_host = request.form.get("internal_host", "").strip()
    internal_port = request.form.get("internal_port", "80").strip()
    scheme = request.form.get("scheme", "http")
    ws_support = request.form.get("ws_support") == "on"
    cf_ssl = request.form.get("cf_ssl") == "on"
    ha_mode = request.form.get("ha_mode") == "on"

    config = _build_npm_config(hostname, internal_host, internal_port, scheme, ws_support, cf_ssl, ha_mode)
    domain = get_options().get("domain", "")
    return render_template(
        "npm_helper.html",
        domain=domain,
        config=config,
        form_data=request.form,
    )


def _build_npm_config(hostname, host, port, scheme, websocket, cf_ssl, ha_mode):
    lines = []
    lines.append(f"# ═══════════════════════════════════════════════════")
    lines.append(f"#  NPM-Konfiguration für: {hostname}")
    lines.append(f"# ═══════════════════════════════════════════════════")
    lines.append("")
    lines.append("# ── Proxy-Host Einstellungen ──────────────────────")
    lines.append(f"#  Domain Names:         {hostname}")
    lines.append(f"#  Scheme:               {scheme}")
    lines.append(f"#  Forward Hostname/IP:  {host}")
    lines.append(f"#  Forward Port:         {port}")
    lines.append(f"#  Cache Assets:         Nein")
    lines.append(f"#  Block Common Exploits: Ja")
    lines.append(f"#  Websockets Support:   {'Ja' if websocket else 'Nein'}")
    lines.append("")

    if cf_ssl:
        lines.append("# ── SSL-Einstellungen ────────────────────────────")
        lines.append("#  SSL Certificate:     Cloudflare Origin Certificate")
        lines.append("#  Force SSL:           Ja")
        lines.append("#  HTTP/2 Support:      Ja")
        lines.append("#  HSTS:                Ja (max-age=31536000)")
        lines.append("")
        lines.append("# ── Cloudflare Dashboard ─────────────────────────")
        lines.append(f"#  DNS-Typ:             CNAME  {hostname} → [Tunnel-ID].cfargotunnel.com")
        lines.append("#  Proxy-Status:        Aktiv (orange Wolke)")
        lines.append("#  SSL/TLS-Modus:       Full (strict)")
        lines.append("#  Minimum TLS:         TLS 1.2")
        lines.append("")

    lines.append("# ── Erweiterte Nginx-Konfiguration ──────────────")
    lines.append("location / {")
    lines.append(f"    proxy_pass {scheme}://{host}:{port};")
    lines.append("    proxy_set_header Host $host;")
    lines.append("    proxy_set_header X-Real-IP $remote_addr;")
    lines.append("    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
    lines.append("    proxy_set_header X-Forwarded-Proto $scheme;")
    if websocket:
        lines.append("    proxy_http_version 1.1;")
        lines.append('    proxy_set_header Upgrade $http_upgrade;')
        lines.append('    proxy_set_header Connection "upgrade";')
    lines.append("    proxy_read_timeout 86400;")
    lines.append("}")

    if ha_mode:
        lines.append("")
        lines.append("# ── Home Assistant configuration.yaml ────────────")
        lines.append("http:")
        lines.append("  use_x_forwarded_for: true")
        lines.append("  trusted_proxies:")
        lines.append("    - 127.0.0.1")
        lines.append("    - ::1")
        lines.append("    # + Cloudflare IPs (siehe Trusted Proxies Tab)")

    return "\n".join(lines)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)

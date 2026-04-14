#!/usr/bin/with-contenv bashio
set -e

bashio::log.info "Starte Cloudflare Route Manager v1.0.2..."

UPDATE_PROXIES=$(bashio::config 'update_trusted_proxies')
LOG_LEVEL=$(bashio::config 'log_level')
DOMAIN=$(bashio::config 'domain')

export INGRESS_PORT=8200
export INGRESS_PATH=$(bashio::addon.ingress_entry 2>/dev/null || echo "")
export LOG_LEVEL="${LOG_LEVEL}"

bashio::log.info "Domain: ${DOMAIN}"
bashio::log.info "Ingress-Pfad: ${INGRESS_PATH}"

if bashio::var.true "${UPDATE_PROXIES}"; then
    bashio::log.info "Aktualisiere Cloudflare trusted_proxies in configuration.yaml..."
    python3 /app/update_proxies.py \
        && bashio::log.info "trusted_proxies erfolgreich aktualisiert" \
        || bashio::log.warning "trusted_proxies konnten nicht aktualisiert werden"
fi

bashio::log.info "Web-Interface gestartet auf Port 8200"
exec python3 /app/app.py

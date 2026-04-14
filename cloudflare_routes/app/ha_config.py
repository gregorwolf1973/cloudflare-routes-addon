import os
import yaml

HA_CONFIG_PATH = "/config/configuration.yaml"

CLOUDFLARE_IPV4 = [
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22",
]

CLOUDFLARE_IPV6 = [
    "2400:cb00::/32",
    "2606:4700::/32",
    "2803:f800::/32",
    "2405:b500::/32",
    "2405:8100::/32",
    "2a06:98c0::/29",
    "2c0f:f248::/32",
]


def read_config():
    if not os.path.exists(HA_CONFIG_PATH):
        return {}
    with open(HA_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_config(config):
    with open(HA_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def get_current_trusted_proxies():
    config = read_config()
    http = config.get("http") or {}
    if not isinstance(http, dict):
        return []
    return http.get("trusted_proxies") or []


def update_trusted_proxies(include_ipv6=True):
    cf_ips = CLOUDFLARE_IPV4[:]
    if include_ipv6:
        cf_ips += CLOUDFLARE_IPV6

    current = get_current_trusted_proxies()
    merged = sorted(set(current) | set(cf_ips))

    config = read_config()
    if not isinstance(config.get("http"), dict):
        config["http"] = {}
    config["http"]["trusted_proxies"] = merged

    write_config(config)
    return merged


def remove_cf_trusted_proxies():
    cf_all = set(CLOUDFLARE_IPV4 + CLOUDFLARE_IPV6)
    current = get_current_trusted_proxies()
    filtered = [ip for ip in current if ip not in cf_all]

    config = read_config()
    if not isinstance(config.get("http"), dict):
        config["http"] = {}
    config["http"]["trusted_proxies"] = filtered

    write_config(config)
    return filtered


def cf_ips_in_config():
    current = set(get_current_trusted_proxies())
    all_cf = CLOUDFLARE_IPV4 + CLOUDFLARE_IPV6
    present = [ip for ip in all_cf if ip in current]
    missing = [ip for ip in all_cf if ip not in current]
    return present, missing

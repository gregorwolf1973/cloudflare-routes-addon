import os
import re
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


# Custom YAML-Loader, der HA-spezifische Tags (!include, !secret, !env_var …)
# einfach ignoriert statt einen Fehler zu werfen.
class _HaLoader(yaml.SafeLoader):
    pass

def _ignore_tag(loader, tag_suffix, node):
    return None

_HaLoader.add_multi_constructor("", _ignore_tag)


def read_config():
    """YAML-Datei lesen und unbekannte Tags (z.B. !include) ignorieren."""
    if not os.path.exists(HA_CONFIG_PATH):
        return {}
    with open(HA_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=_HaLoader) or {}


def _read_text():
    if not os.path.exists(HA_CONFIG_PATH):
        return ""
    with open(HA_CONFIG_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(text):
    with open(HA_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(text)


def _uses_http_include(text):
    """True, wenn http: per !include eingebunden wird – dann können wir nicht schreiben."""
    return bool(re.search(r"^http:\s*!include", text, re.MULTILINE))


def _build_proxies_block(ips):
    ip_lines = "\n".join(f"    - {ip}" for ip in sorted(ips))
    return f"  trusted_proxies:\n{ip_lines}"


def get_current_trusted_proxies():
    config = read_config()
    http = config.get("http") or {}
    if not isinstance(http, dict):
        return []
    return http.get("trusted_proxies") or []


def update_trusted_proxies(include_ipv6=True):
    cf_ips = set(CLOUDFLARE_IPV4)
    if include_ipv6:
        cf_ips |= set(CLOUDFLARE_IPV6)

    current = set(get_current_trusted_proxies())
    merged = sorted(current | cf_ips)

    text = _read_text()

    if _uses_http_include(text):
        raise Exception(
            "http: verwendet !include – bitte trusted_proxies manuell in der "
            "eingebundenen Datei eintragen"
        )

    block = _build_proxies_block(merged)

    if re.search(r"^  trusted_proxies:", text, re.MULTILINE):
        # Vorhandenen Block ersetzen
        text = re.sub(
            r"^  trusted_proxies:(?:\n    -[^\n]*)*",
            block,
            text,
            flags=re.MULTILINE,
        )
    elif re.search(r"^http:", text, re.MULTILINE):
        # Unter bestehender http:-Sektion einfügen
        text = re.sub(r"^(http:)", r"\1\n" + block, text, flags=re.MULTILINE)
    else:
        # Neue http:-Sektion anhängen
        text = text.rstrip("\n") + f"\n\nhttp:\n{block}\n"

    _write_text(text)
    return merged


def remove_cf_trusted_proxies():
    cf_all = set(CLOUDFLARE_IPV4 + CLOUDFLARE_IPV6)
    current = get_current_trusted_proxies()
    filtered = sorted(ip for ip in current if ip not in cf_all)

    text = _read_text()

    if _uses_http_include(text):
        raise Exception(
            "http: verwendet !include – bitte trusted_proxies manuell entfernen"
        )

    if re.search(r"^  trusted_proxies:", text, re.MULTILINE):
        block = _build_proxies_block(filtered) if filtered else "  trusted_proxies: []"
        text = re.sub(
            r"^  trusted_proxies:(?:\n    -[^\n]*)*",
            block,
            text,
            flags=re.MULTILINE,
        )
        _write_text(text)

    return filtered


def cf_ips_in_config():
    current = set(get_current_trusted_proxies())
    all_cf = CLOUDFLARE_IPV4 + CLOUDFLARE_IPV6
    present = [ip for ip in all_cf if ip in current]
    missing = [ip for ip in all_cf if ip not in current]
    return present, missing

import requests


class CloudflareAPI:
    BASE_URL = "https://api.cloudflare.com/client/v4"

    def __init__(self, options):
        self.api_token = options.get("cloudflare_api_token", "")
        self.email = options.get("cloudflare_email", "")
        self.global_key = options.get("cloudflare_global_api_key", "")
        self.zone_id = options.get("zone_id", "")
        self.account_id = options.get("account_id", "")

    def _headers(self):
        if self.api_token:
            return {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
        return {
            "X-Auth-Email": self.email,
            "X-Auth-Key": self.global_key,
            "Content-Type": "application/json",
        }

    def _check(self, data):
        if not data.get("success"):
            errors = data.get("errors", [{"message": "Unbekannter Fehler"}])
            raise Exception(errors[0].get("message", "Unbekannter Fehler"))
        return data["result"]

    def _get(self, path, params=None):
        r = requests.get(
            f"{self.BASE_URL}{path}", headers=self._headers(), params=params, timeout=15
        )
        r.raise_for_status()
        return self._check(r.json())

    def _post(self, path, payload):
        r = requests.post(
            f"{self.BASE_URL}{path}", headers=self._headers(), json=payload, timeout=15
        )
        r.raise_for_status()
        return self._check(r.json())

    def _put(self, path, payload):
        r = requests.put(
            f"{self.BASE_URL}{path}", headers=self._headers(), json=payload, timeout=15
        )
        r.raise_for_status()
        return self._check(r.json())

    def _delete(self, path):
        r = requests.delete(
            f"{self.BASE_URL}{path}", headers=self._headers(), timeout=15
        )
        r.raise_for_status()
        return self._check(r.json())

    # --- Token / Auth ---
    def verify_token(self):
        return self._get("/user/tokens/verify")

    # --- Zone ---
    def get_zone_info(self):
        return self._get(f"/zones/{self.zone_id}")

    # --- DNS ---
    def list_dns_records(self):
        return self._get(
            f"/zones/{self.zone_id}/dns_records",
            params={"per_page": 200},
        )

    def create_dns_record(self, record_type, name, content, ttl=1, proxied=True):
        return self._post(
            f"/zones/{self.zone_id}/dns_records",
            {"type": record_type, "name": name, "content": content, "ttl": ttl, "proxied": proxied},
        )

    def update_dns_record(self, record_id, record_type, name, content, ttl=1, proxied=True):
        return self._put(
            f"/zones/{self.zone_id}/dns_records/{record_id}",
            {"type": record_type, "name": name, "content": content, "ttl": ttl, "proxied": proxied},
        )

    def delete_dns_record(self, record_id):
        return self._delete(f"/zones/{self.zone_id}/dns_records/{record_id}")

    # --- Tunnels ---
    def list_tunnels(self):
        if not self.account_id:
            return []
        return self._get(
            f"/accounts/{self.account_id}/cfd_tunnel",
            params={"is_deleted": "false", "per_page": 100},
        )

    def get_tunnel_config(self, tunnel_id):
        return self._get(
            f"/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}/configurations"
        )

    def update_tunnel_config(self, tunnel_id, config):
        return self._put(
            f"/accounts/{self.account_id}/cfd_tunnel/{tunnel_id}/configurations",
            config,
        )

    # --- Cloudflare IPs ---
    def get_cloudflare_ips(self):
        try:
            r = requests.get(f"{self.BASE_URL}/ips", timeout=10)
            data = r.json()
            if data.get("success"):
                return data["result"]
        except Exception:
            pass
        return None

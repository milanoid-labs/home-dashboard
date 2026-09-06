"""
Client for the Eaton xComfort Smart Home Controller (SHC) local API.

The SHC (model CHCA-00/01) — not to be confused with the newer, unrelated
"xComfort Bridge" product — exposes a plain HTTP + JSON-RPC 2.0 API using
the exact same login as its WebAdmin console / the mobile app:

  1. HTTP Basic Auth against the controller's root URL sets a JSESSIONID
     session cookie.
  2. Every read/write is a JSON-RPC 2.0 POST to `/remote/json-rpc`.

Reference implementations this is based on: olesk75/xComfortAPI and the
Home Assistant integration plamish/xcomfort.
"""

from __future__ import annotations

import logging
import threading
import time

import requests

logger = logging.getLogger(__name__)

# Which control operations make sense for a given device `type`. Devices
# with no entry here (temperature/humidity/smoke/wind sensors, etc.) are
# treated as read-only.
_OPERATIONS_BY_TYPE = {
    "LightActuator": ["on", "off", "toggle"],
    "SwitchActuator": ["on", "off", "toggle"],
    "DimActuator": ["on", "off", "toggle"],
    "ShutterActuator": ["open", "close", "stop", "stepOpen", "stepClose"],
}


class SHCError(Exception):
    """Raised when the controller can't be reached or rejects a request."""


def _normalize_device(raw: dict) -> dict:
    """Map a raw StatusControlFunction/getDevices entry onto our Device shape."""
    device_type = raw.get("type", "")
    operations = _OPERATIONS_BY_TYPE.get(device_type, [])
    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "type": device_type,
        "value": raw.get("value"),
        "unit": raw.get("unit"),
        "operations": operations,
        "controllable": bool(operations),
    }


class SHCClient:
    def __init__(
        self, base_url: str, username: str, password: str, session_ttl: int = 300
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session_ttl = session_ttl
        self._session: requests.Session | None = None
        self._session_started_at: float = 0.0
        self._lock = threading.Lock()

    def _ensure_session(self) -> requests.Session:
        with self._lock:
            now = time.monotonic()
            stale = (now - self._session_started_at) > self.session_ttl
            if self._session is None or stale:
                self._session = self._login()
                self._session_started_at = now
            return self._session

    def _login(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": "home-dashboard"})
        try:
            session.get(self.base_url, timeout=10)
            resp = session.post(
                self.base_url, auth=(self.username, self.password), timeout=10
            )
        except requests.RequestException as exc:
            raise SHCError(
                f"Could not reach the SHC at {self.base_url}: {exc}"
            ) from exc
        if resp.status_code == 401:
            raise SHCError("Invalid SHC username/password")
        resp.raise_for_status()
        return session

    def _rpc(self, method: str, params=None, retry: bool = True):
        if params is None:
            params = ["", ""]
        session = self._ensure_session()
        try:
            resp = session.post(
                f"{self.base_url}/remote/json-rpc",
                json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
                headers={"Accept": "application/json, text/javascript, */*; q=0.01"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SHCError(f"SHC request failed calling {method}: {exc}") from exc

        if resp.status_code in (401, 403) and retry:
            # Session likely expired server-side - force a fresh login and
            # retry exactly once.
            with self._lock:
                self._session = None
            return self._rpc(method, params, retry=False)

        try:
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as exc:
            raise SHCError(
                f"SHC returned an unexpected response for {method}: {exc}"
            ) from exc

        if "error" in data:
            raise SHCError(f"SHC RPC error calling {method}: {data['error']}")
        return data.get("result", [])

    def get_zones(self) -> list:
        return self._rpc("HFM/getZones", [""])

    def get_devices(self, zone_id: str) -> list:
        return self._rpc("StatusControlFunction/getDevices", [zone_id, ""])

    def get_all_zones(self) -> list[dict]:
        """Every zone, each with its normalized device list."""
        zones = []
        for zone in self.get_zones():
            raw_devices = self.get_devices(zone["zoneId"])
            zones.append(
                {
                    "zone_id": zone["zoneId"],
                    "zone_name": zone["zoneName"],
                    "devices": [_normalize_device(d) for d in raw_devices],
                }
            )
        return zones

    def control_device(self, zone_id: str, device_id: str, state: str) -> bool:
        result = self._rpc(
            "StatusControlFunction/controlDevice", [zone_id, device_id, state]
        )
        if isinstance(result, dict):
            return result.get("status", "ok") == "ok"
        return True

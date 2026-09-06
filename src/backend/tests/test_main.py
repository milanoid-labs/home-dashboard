from fastapi.testclient import TestClient

from backend.main import app, get_client
from backend.shc_client import SHCError


class FakeClient:
    def __init__(self, zones=None, raise_on_control=False):
        self._zones = zones or []
        self._raise_on_control = raise_on_control

    def get_all_zones(self):
        return self._zones

    def control_device(self, zone_id, device_id, state):
        if self._raise_on_control:
            raise SHCError("boom")
        return True


class UnreachableClient:
    def get_all_zones(self):
        raise SHCError("Could not reach the SHC")


ZONES = [
    {
        "zone_id": "hz_1",
        "zone_name": "obyvaci prostor",
        "devices": [
            {
                "id": "xCo:1_u0",
                "name": "sv obyvak",
                "type": "LightActuator",
                "value": "OFF",
                "unit": None,
                "operations": ["on", "off", "toggle"],
                "controllable": True,
            }
        ],
    }
]


def _use(fake):
    app.dependency_overrides[get_client] = lambda: fake


def _clear():
    app.dependency_overrides.clear()


def test_root():
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_read_zones_ok():
    _use(FakeClient(zones=ZONES))
    client = TestClient(app)
    resp = client.get("/zones")
    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["zone_id"] == "hz_1"
    assert body[0]["devices"][0]["name"] == "sv obyvak"
    _clear()


def test_read_zones_shc_unreachable():
    _use(UnreachableClient())
    client = TestClient(app)
    resp = client.get("/zones")
    assert resp.status_code == 502
    _clear()


def test_control_device_ok():
    _use(FakeClient())
    client = TestClient(app)
    resp = client.post("/zones/hz_1/devices/xCo:1_u0/control", json={"state": "on"})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    _clear()


def test_control_device_shc_error():
    _use(FakeClient(raise_on_control=True))
    client = TestClient(app)
    resp = client.post("/zones/hz_1/devices/xCo:1_u0/control", json={"state": "on"})
    assert resp.status_code == 502
    _clear()


def test_control_device_rejects_invalid_state():
    _use(FakeClient())
    client = TestClient(app)
    resp = client.post(
        "/zones/hz_1/devices/xCo:1_u0/control", json={"state": "not-a-state"}
    )
    assert resp.status_code == 422
    _clear()


def test_control_device_accepts_colon_in_device_id():
    _use(FakeClient())
    client = TestClient(app)
    resp = client.post(
        "/zones/hz_1/devices/xCo:6602052_u0/control", json={"state": "toggle"}
    )
    assert resp.status_code == 200
    _clear()

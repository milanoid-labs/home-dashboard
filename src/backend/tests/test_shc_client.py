import pytest

from backend.shc_client import SHCClient, SHCError, _normalize_device


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data if json_data is not None else {}

    def raise_for_status(self):
        if self.status_code >= 400 and self.status_code not in (401, 403):
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def get(self, *args, **kwargs):
        return FakeResponse(200)

    def post(self, url, *args, **kwargs):
        self.calls.append((url, kwargs))
        return self._responses.pop(0)


def test_normalize_device_light_actuator():
    d = _normalize_device(
        {"id": "xCo:1_u0", "name": "sv obyvak", "type": "LightActuator", "value": "OFF"}
    )
    assert d["controllable"] is True
    assert d["operations"] == ["on", "off", "toggle"]
    assert d["unit"] is None


def test_normalize_device_shutter_actuator():
    d = _normalize_device(
        {
            "id": "xCo:2_u0",
            "name": "roleta obyvak",
            "type": "ShutterActuator",
            "value": "OTEVŘENO",
        }
    )
    assert d["controllable"] is True
    assert d["operations"] == ["open", "close", "stop", "stepOpen", "stepClose"]


def test_normalize_device_sensor_is_readonly():
    d = _normalize_device(
        {
            "id": "xCo:3_u0",
            "name": "termostat obyvak",
            "type": "TemperatureSensor",
            "value": "25.9",
            "unit": "°C",
        }
    )
    assert d["controllable"] is False
    assert d["operations"] == []
    assert d["unit"] == "°C"


def test_login_invalid_credentials(monkeypatch):
    client = SHCClient("http://shc.example", "admin", "wrong")

    class FakeAuthSession:
        def __init__(self):
            self.headers = {}

        def get(self, *a, **kw):
            return FakeResponse(200)

        def post(self, *a, **kw):
            return FakeResponse(401)

    monkeypatch.setattr(
        "backend.shc_client.requests.Session", lambda: FakeAuthSession()
    )
    with pytest.raises(SHCError, match="Invalid SHC username/password"):
        client._ensure_session()


def test_get_zones(monkeypatch):
    client = SHCClient("http://shc.example", "admin", "secret")
    fake_session = FakeSession(
        [
            FakeResponse(
                200,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": [{"zoneId": "hz_1", "zoneName": "living room"}],
                },
            )
        ]
    )
    monkeypatch.setattr(client, "_ensure_session", lambda: fake_session)
    assert client.get_zones() == [{"zoneId": "hz_1", "zoneName": "living room"}]


def test_get_all_zones_normalizes_devices(monkeypatch):
    client = SHCClient("http://shc.example", "admin", "secret")
    responses = FakeSession(
        [
            FakeResponse(
                200, {"result": [{"zoneId": "hz_1", "zoneName": "living room"}]}
            ),
            FakeResponse(
                200,
                {
                    "result": [
                        {
                            "id": "xCo:1_u0",
                            "name": "sv obyvak",
                            "type": "LightActuator",
                            "value": "OFF",
                        }
                    ]
                },
            ),
        ]
    )
    monkeypatch.setattr(client, "_ensure_session", lambda: responses)
    zones = client.get_all_zones()
    assert zones == [
        {
            "zone_id": "hz_1",
            "zone_name": "living room",
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


def test_rpc_error_raises(monkeypatch):
    client = SHCClient("http://shc.example", "admin", "secret")
    fake_session = FakeSession([FakeResponse(200, {"error": "boom"})])
    monkeypatch.setattr(client, "_ensure_session", lambda: fake_session)
    with pytest.raises(SHCError, match="boom"):
        client.get_zones()


def test_rpc_retries_once_on_401(monkeypatch):
    client = SHCClient("http://shc.example", "admin", "secret")
    fake_session = FakeSession(
        [
            FakeResponse(401),
            FakeResponse(
                200, {"result": [{"zoneId": "hz_1", "zoneName": "living room"}]}
            ),
        ]
    )
    monkeypatch.setattr(client, "_ensure_session", lambda: fake_session)
    assert client.get_zones() == [{"zoneId": "hz_1", "zoneName": "living room"}]
    assert len(fake_session.calls) == 2


def test_control_device_returns_true_for_bare_result(monkeypatch):
    client = SHCClient("http://shc.example", "admin", "secret")
    fake_session = FakeSession([FakeResponse(200, {"result": []})])
    monkeypatch.setattr(client, "_ensure_session", lambda: fake_session)
    assert client.control_device("hz_1", "xCo:1_u0", "on") is True


def test_control_device_reads_status_dict(monkeypatch):
    client = SHCClient("http://shc.example", "admin", "secret")
    fake_session = FakeSession([FakeResponse(200, {"result": {"status": "error"}})])
    monkeypatch.setattr(client, "_ensure_session", lambda: fake_session)
    assert client.control_device("hz_1", "xCo:1_u0", "on") is False

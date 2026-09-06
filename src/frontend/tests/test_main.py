import requests
import responses

from frontend.main import EXCLUDED_ZONES

API_URL = "http://localhost:8001"

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
            },
            {
                "id": "xCo:2_u0",
                "name": "roleta obyvak",
                "type": "ShutterActuator",
                "value": "ZAVŘENO",
                "unit": None,
                "operations": ["open", "close", "stop", "stepOpen", "stepClose"],
                "controllable": True,
            },
            {
                "id": "xCo:3_u0",
                "name": "termostat obyvak",
                "type": "TemperatureSensor",
                "value": "25.9",
                "unit": "°C",
                "operations": [],
                "controllable": False,
            },
        ],
    },
    {
        "zone_id": "hz_6",
        "zone_name": "servis",
        "devices": [
            {
                "id": "xCo:9_u0",
                "name": "pozarni cidlo",
                "type": "BinarySmokeSensor",
                "value": "?",
                "unit": None,
                "operations": [],
                "controllable": False,
            }
        ],
    },
]


@responses.activate
def test_index_renders_devices(client):
    responses.add(responses.GET, f"{API_URL}/zones", json=ZONES, status=200)
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "sv obyvak" in body
    assert "roleta obyvak" in body
    assert "25.9" in body


@responses.activate
def test_index_excludes_servis_zone(client):
    responses.add(responses.GET, f"{API_URL}/zones", json=ZONES, status=200)
    resp = client.get("/")
    body = resp.get_data(as_text=True)
    assert "pozarni cidlo" not in body
    assert "servis" not in EXCLUDED_ZONES or "hz_6" not in body


@responses.activate
def test_index_shows_error_banner_when_backend_down(client):
    responses.add(
        responses.GET, f"{API_URL}/zones", body=requests.exceptions.ConnectionError()
    )
    resp = client.get("/")
    assert resp.status_code == 200
    assert "reach the dashboard backend" in resp.get_data(as_text=True)


@responses.activate
def test_control_valid_action_calls_backend_and_redirects(client):
    control_url = f"{API_URL}/zones/hz_1/devices/xCo:1_u0/control"
    responses.add(responses.POST, control_url, json={"ok": True}, status=200)
    resp = client.post("/control/hz_1/xCo:1_u0/toggle")
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/"
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == control_url


@responses.activate
def test_control_rejects_unknown_action(client):
    resp = client.post("/control/hz_1/xCo:1_u0/not-a-real-action")
    assert resp.status_code == 302
    assert len(responses.calls) == 0


@responses.activate
def test_control_backend_error_still_redirects(client):
    control_url = f"{API_URL}/zones/hz_1/devices/xCo:1_u0/control"
    responses.add(responses.POST, control_url, status=502)
    resp = client.post("/control/hz_1/xCo:1_u0/on")
    assert resp.status_code == 302


@responses.activate
def test_health_reports_ok_when_backend_healthy(client):
    responses.add(
        responses.GET, f"{API_URL}/health", json={"status": "healthy"}, status=200
    )
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "healthy", "api_connectivity": True}


@responses.activate
def test_health_reports_unhealthy_when_backend_down(client):
    responses.add(
        responses.GET, f"{API_URL}/health", body=requests.exceptions.ConnectionError()
    )
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.get_json()["api_connectivity"] is False

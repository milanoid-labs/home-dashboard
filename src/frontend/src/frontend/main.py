import logging
import os

import requests
from flask import Flask, redirect, render_template, url_for

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config["API_URL"] = os.getenv("API_URL", "http://localhost:8001")
app.config["API_TIMEOUT"] = int(os.getenv("API_TIMEOUT", "10"))
app.config["PORT"] = int(os.getenv("FRONTEND_PORT", "8080"))
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "False").lower() == "true"
app.config["HOST"] = os.getenv("FRONTEND_HOST", "0.0.0.0")

# Mirrors backend.models.ControlState - kept in sync manually since the two
# services don't share a package.
VALID_ACTIONS = {
    "on",
    "off",
    "toggle",
    "open",
    "close",
    "stop",
    "stepOpen",
    "stepClose",
}

# Human labels/icons for a device's `type`, used to pick the card layout.
ACTUATOR_TYPES = {"LightActuator", "SwitchActuator", "DimActuator"}
SHUTTER_TYPES = {"ShutterActuator"}

# Zones left out of the dashboard for now - "servis" is diagnostic/utility
# sensors (analog inputs, wind switches, smoke sensor), not something to
# act on day to day. Revisit if that changes.
EXCLUDED_ZONES = {"servis"}


def get_zones():
    """Fetch all zones/devices from the backend API.

    Returns (zones, error) - error is None on success, or a short message
    for display when the backend/controller can't be reached.
    """
    try:
        resp = requests.get(
            f"{app.config['API_URL']}/zones", timeout=app.config["API_TIMEOUT"]
        )
        resp.raise_for_status()
        zones = resp.json()
        zones = [z for z in zones if z["zone_name"].lower() not in EXCLUDED_ZONES]
        return zones, None
    except requests.RequestException as e:
        logger.error(f"Error fetching zones: {e}")
        return [], "Can't reach the dashboard backend right now."


@app.route("/")
def index():
    zones, error = get_zones()
    return render_template(
        "index.html",
        zones=zones,
        error=error,
        actuator_types=ACTUATOR_TYPES,
        shutter_types=SHUTTER_TYPES,
    )


@app.route("/control/<zone_id>/<device_id>/<action>", methods=["POST"])
def control(zone_id, device_id, action):
    if action not in VALID_ACTIONS:
        logger.warning(f"Rejected invalid action '{action}' for device {device_id}")
        return redirect(url_for("index"))
    try:
        resp = requests.post(
            f"{app.config['API_URL']}/zones/{zone_id}/devices/{device_id}/control",
            json={"state": action},
            timeout=app.config["API_TIMEOUT"],
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error sending '{action}' to device {device_id}: {e}")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    """Health check endpoint for monitoring - also checks backend connectivity"""
    try:
        resp = requests.get(
            f"{app.config['API_URL']}/health", timeout=app.config["API_TIMEOUT"]
        )
        api_ok = resp.status_code == 200
    except requests.RequestException:
        api_ok = False

    status = "healthy" if api_ok else "unhealthy"
    return {"status": status, "api_connectivity": api_ok}, 200 if api_ok else 503


def main():
    """Entry point for running the frontend server"""
    logger.info("Starting Home Dashboard frontend")
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()

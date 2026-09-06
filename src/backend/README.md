# home-dashboard-backend

FastAPI backend that talks to the Eaton xComfort Smart Home Controller
(SHC) on the local LAN and exposes a small REST API for the frontend.

## Endpoints

- `GET /health` — liveness check (does not call the SHC)
- `GET /zones` — every zone and its devices, with live values
- `POST /zones/{zone_id}/devices/{device_id}/control` — control a device,
  body `{"state": "on"}` (see `ControlState` in `models.py` for the full
  set of accepted states)

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `SHC_URL` | `http://192.168.1.56` | Base URL of the controller |
| `SHC_USERNAME` | `admin` | Same login as the WebAdmin console / app |
| `SHC_PASSWORD` | *(empty)* | **Required** — never commit a value |
| `SHC_SESSION_TTL` | `300` | Seconds before re-authenticating to the SHC |
| `API_HOST` / `API_PORT` | `0.0.0.0` / `8001` | Where uvicorn listens |
| `CORS_ALLOW_ORIGINS` | `*` | Comma-separated list, or `*` |

## Run locally

```bash
uv sync --dev
SHC_PASSWORD=... uv run home-dashboard-api
```

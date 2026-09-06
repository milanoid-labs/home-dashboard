# home-dashboard-frontend

Mobile-first web UI for controlling the Eaton xComfort smart home
controller, via the `home-dashboard-backend` API. Server-rendered
(Flask + Jinja) — no build step, no JS framework.

## Configuration (environment variables)

| Variable | Default | Purpose |
|---|---|---|
| `API_URL` | `http://localhost:8001` | Base URL of `home-dashboard-backend` |
| `API_TIMEOUT` | `10` | Seconds before giving up on the backend |
| `FRONTEND_HOST` / `FRONTEND_PORT` | `0.0.0.0` / `8080` | Where Flask listens |

## Run locally

```bash
uv sync --dev
API_URL=http://localhost:8001 uv run home-dashboard-web
```

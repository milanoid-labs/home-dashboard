# home-dashboard

A mobile-first web dashboard for controlling my Eaton xComfort Smart Home
Controller (SHC) — the shades and light in the house — over the LAN,
without going through the (slow, occasionally flaky) iOS app or the
controller's own web console.

**This repo is public.** SHC credentials (URL/username/password) are
never committed here — they reach the backend only via a Kubernetes
Secret at deploy time. See `src/backend/README.md`.

## Layout

- `src/backend` — FastAPI service that talks to the SHC's local JSON-RPC
  API and exposes a small REST API (`/zones`, device control)
- `src/frontend` — Flask + server-rendered HTML frontend: one page,
  cards per device grouped by room, big touch targets for shades,
  manual refresh (the SHC API has no push/live-update channel)

Each has its own README with configuration and local-run instructions.

## Access model

LAN-only, no login — this only runs inside my home network.

## Deployment

Runs on my homelab Kubernetes cluster via ArgoCD, mirroring the
`devops-study-app` deployment pattern (see the `milanoid-labs/homelab-cluster`
repo, `apps/argocd/home-dashboard/`).

## CI/CD

- `backend-tests.yaml` / `frontend-tests.yaml` — lint (ruff), test
  (pytest, ≥80% coverage), build + Trivy scan on every PR touching that
  component
- `docker-build-push.yaml` — builds and pushes images to GHCR on
  `backend*` / `frontend*` tags
- `release-please.yaml` — per-component versioning (`backend`/`frontend`
  are released independently)

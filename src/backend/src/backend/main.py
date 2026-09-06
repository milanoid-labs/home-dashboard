import logging

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    API_HOST,
    API_PORT,
    API_RELOAD,
    APP_NAME,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_ORIGINS,
    SHC_PASSWORD,
    SHC_SESSION_TTL,
    SHC_URL,
    SHC_USERNAME,
)
from .models import ControlRequest, ControlResult, Zone
from .shc_client import SHCClient, SHCError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME,
    description="API for controlling my Eaton xComfort smart home controller",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

_client: SHCClient | None = None


def get_client() -> SHCClient:
    """FastAPI dependency - lazily builds a single shared SHCClient.

    Overridden in tests via `app.dependency_overrides` so tests never hit
    the real controller.
    """
    global _client
    if _client is None:
        _client = SHCClient(
            SHC_URL, SHC_USERNAME, SHC_PASSWORD, session_ttl=SHC_SESSION_TTL
        )
    return _client


@app.get("/")
async def root():
    """Root endpoint returning API information"""
    return {"message": f"{APP_NAME} API"}


@app.get("/health")
async def health():
    """Health endpoint for kubernetes probes - does not call the SHC"""
    return {"status": "healthy"}


@app.get("/zones", response_model=list[Zone])
async def read_zones(client: SHCClient = Depends(get_client)):
    """Every zone and its devices, with live values"""
    try:
        return client.get_all_zones()
    except SHCError as e:
        logger.error(f"Error fetching zones: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/zones/{zone_id}/devices/{device_id}/control", response_model=ControlResult)
async def control_device(
    zone_id: str,
    device_id: str,
    request: ControlRequest,
    client: SHCClient = Depends(get_client),
):
    """Send a control command to one device"""
    try:
        ok = client.control_device(zone_id, device_id, request.state)
        return ControlResult(ok=ok)
    except SHCError as e:
        logger.error(f"Error controlling {device_id}: {e}")
        raise HTTPException(status_code=502, detail=str(e))


def main():
    """Entry point for running the API server"""
    logger.info(f"Starting {APP_NAME} API")
    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT, reload=API_RELOAD)


if __name__ == "__main__":
    main()

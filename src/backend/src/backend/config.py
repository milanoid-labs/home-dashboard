import os


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


def _parse_list(env_name: str, default: str = "*") -> list[str]:
    """Comma-separated env var -> list. "*" (the default) means "any"."""
    value = os.getenv(env_name, default)
    if value == "*":
        return ["*"]
    return [item.strip() for item in value.split(",") if item.strip()]


# Application settings
APP_NAME = os.getenv("APP_NAME", "Home Dashboard")

# API server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))
API_RELOAD = _parse_bool(os.getenv("API_RELOAD", "false"))

# Eaton xComfort Smart Home Controller connection.
# SHC_PASSWORD defaults to empty on purpose - a real value must come from
# a k8s Secret / env var at deploy time, never committed to this (public)
# repo.
SHC_URL = os.getenv("SHC_URL", "http://192.168.1.56")
SHC_USERNAME = os.getenv("SHC_USERNAME", "admin")
SHC_PASSWORD = os.getenv("SHC_PASSWORD", "")

# How long a cached SHC login session is trusted before re-authenticating.
SHC_SESSION_TTL = int(os.getenv("SHC_SESSION_TTL", "300"))

# CORS. Comma-separated values, e.g. CORS_ALLOW_ORIGINS=http://a,http://b.
# "*" (the default) means "any".
CORS_ALLOW_ORIGINS = _parse_list("CORS_ALLOW_ORIGINS")
CORS_ALLOW_METHODS = _parse_list("CORS_ALLOW_METHODS")
CORS_ALLOW_HEADERS = _parse_list("CORS_ALLOW_HEADERS")
# Default to False: paired with CORS_ALLOW_ORIGINS="*" (also the
# default), allow_credentials=True would let any site that can reach this
# LAN service read authenticated responses from a visiting browser. Only
# turn this on if CORS_ALLOW_ORIGINS is also locked down to specific
# origins.
CORS_ALLOW_CREDENTIALS = _parse_bool(os.getenv("CORS_ALLOW_CREDENTIALS", "false"))

import importlib
from unittest import mock

from backend import config


def test_defaults():
    importlib.reload(config)
    assert config.APP_NAME == "Home Dashboard"
    assert config.API_HOST == "0.0.0.0"
    assert config.API_PORT == 8001
    assert config.API_RELOAD is False
    assert config.SHC_URL == "http://192.168.1.56"
    assert config.SHC_USERNAME == "admin"
    assert config.SHC_PASSWORD == ""
    assert config.SHC_SESSION_TTL == 300
    assert config.CORS_ALLOW_ORIGINS == ["*"]
    assert config.CORS_ALLOW_METHODS == ["*"]
    assert config.CORS_ALLOW_HEADERS == ["*"]
    assert config.CORS_ALLOW_CREDENTIALS is False


@mock.patch.dict(
    "os.environ",
    {
        "API_PORT": "9999",
        "API_RELOAD": "true",
        "SHC_URL": "http://shc.example",
        "SHC_USERNAME": "someone",
        "SHC_PASSWORD": "secret",
        "SHC_SESSION_TTL": "60",
        "CORS_ALLOW_ORIGINS": "http://a.example,http://b.example",
        "CORS_ALLOW_CREDENTIALS": "false",
    },
)
def test_overrides_from_env():
    importlib.reload(config)
    try:
        assert config.API_PORT == 9999
        assert config.API_RELOAD is True
        assert config.SHC_URL == "http://shc.example"
        assert config.SHC_USERNAME == "someone"
        assert config.SHC_PASSWORD == "secret"
        assert config.SHC_SESSION_TTL == 60
        assert config.CORS_ALLOW_ORIGINS == ["http://a.example", "http://b.example"]
        assert config.CORS_ALLOW_CREDENTIALS is False
    finally:
        importlib.reload(config)

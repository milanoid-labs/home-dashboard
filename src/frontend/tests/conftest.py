import pytest

from frontend.main import app as flask_app

# Tests stub HTTP calls against this fixed URL (see API_URL in
# test_main.py). Set it explicitly here rather than relying on whatever
# API_URL happened to be in the environment at import time, so the tests
# stay hermetic regardless of how/where they're run.
TEST_API_URL = "http://localhost:8001"


@pytest.fixture
def app():
    flask_app.config.update(TESTING=True, API_URL=TEST_API_URL)
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()

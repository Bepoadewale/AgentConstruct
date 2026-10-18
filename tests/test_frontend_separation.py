import pytest
from davdeploy.main import app, configure_frontend_cors, parse_frontend_origins
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_control_plane_root_is_json_and_has_no_static_mount():
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.json() == {
        "product": "davdeploy",
        "surface": "control-plane-api",
        "api_version": "v1",
        "openapi": "/openapi.json",
    }
    assert all(getattr(route, "name", None) != "web" for route in app.routes)


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "https://console.example.com/path",
        "https://console.example.com?preview=true",
        "http://console.example.com",
        "javascript:alert(1)",
    ],
)
def test_frontend_origins_fail_closed(value: str):
    with pytest.raises(RuntimeError):
        parse_frontend_origins(value)


def test_frontend_origins_are_exact_deduplicated_origins():
    assert parse_frontend_origins(
        "https://console.example.com/, http://localhost:5173, https://console.example.com"
    ) == ["https://console.example.com", "http://localhost:5173"]


def test_cors_allows_only_the_configured_origin_without_credentials():
    test_app = FastAPI()
    configure_frontend_cors(test_app, ["https://console.example.com"])

    @test_app.get("/resource")
    def resource():
        return {"ok": True}

    client = TestClient(test_app)
    allowed = client.options(
        "/resource",
        headers={
            "Origin": "https://console.example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    denied = client.options(
        "/resource",
        headers={
            "Origin": "https://attacker.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://console.example.com"
    assert "access-control-allow-credentials" not in allowed.headers
    assert "access-control-allow-origin" not in denied.headers

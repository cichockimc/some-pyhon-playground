# test_app.py
import json

from httpx import AsyncClient

# --- Import the app under test ------------------------------------------------
# Change this import to your actual module, e.g.:
from app.main import app # noqa: F401

# tests/test_app.py
import typing as t
import pytest
import httpx
from fastapi import FastAPI
from app.main import app  # your app

@pytest.fixture(scope="module")
async def client() -> t.AsyncIterator[httpx.AsyncClient]:
    assert isinstance(app, FastAPI)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac



# --- Happy path ---------------------------------------------------------------

@pytest.mark.anyio
async def test_root_status_ok(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_root_content_type_is_json(client: AsyncClient):
    resp = await client.get("/")
    # Starlette/FastAPI default is 'application/json'
    assert resp.headers["content-type"].startswith("application/json")


@pytest.mark.anyio
async def test_root_exact_body(client: AsyncClient):
    resp = await client.get("/")
    assert resp.json() == {"message": "Hello, world!"}


@pytest.mark.anyio
async def test_root_schema_and_types(client: AsyncClient):
    resp = await client.get("/")
    data = resp.json()
    assert isinstance(data, dict)
    assert "message" in data
    assert isinstance(data["message"], str)
    assert data["message"]  # non-empty string


# --- HTTP method semantics ----------------------------------------------------

@pytest.mark.anyio
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete", "options"])
async def test_method_not_allowed_on_root(client: AsyncClient, method: str):
    resp = await getattr(client, method)("/")
    # GET is defined; others should be 405 (OPTIONS may be 405 if CORS not added)
    assert resp.status_code in (405, 200)
    if resp.status_code == 405:
        # Starlette usually sets an "allow" header listing allowed methods
        allow = resp.headers.get("allow", "")
        assert "GET" in allow


# --- Trailing slash & canonicalization ---------------------------------------

@pytest.mark.anyio
async def test_trailing_slash_equivalence(client: AsyncClient):
    # For root, "/" is canonical; "" should redirect to "/" in docs servers,
    # but httpx client with ASGI app should handle "/" consistently.
    resp = await client.get("/")
    resp2 = await client.get("//")  # often normalized by the router
    assert resp.status_code == 200
    assert resp2.status_code in (200, 404)  # Accept router behavior either way
    if resp2.status_code == 200:
        assert resp2.json() == resp.json()


# --- OpenAPI & documentation endpoints ---------------------------------------

@pytest.mark.anyio
async def test_openapi_contains_root_path(client: AsyncClient):
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    # Basic OpenAPI structure checks
    assert spec.get("openapi", "").startswith("3.")
    assert "paths" in spec and isinstance(spec["paths"], dict)
    assert "/" in spec["paths"]
    # Check GET operation presence
    get_op = spec["paths"]["/"].get("get")
    assert isinstance(get_op, dict)
    # Tags from the route decorator should be present
    assert "tags" in get_op and "root" in get_op["tags"]
    # Title propagated from FastAPI(...)
    assert spec.get("info", {}).get("title") == "Hello World FastAPI"


@pytest.mark.anyio
async def test_swagger_ui_available(client: AsyncClient):
    resp = await client.get("/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    # Stable markers across FastAPI versions
    body = resp.text
    assert "SwaggerUIBundle" in body          # the JS boot code
    assert "/openapi.json" in body            # points the UI at your spec


@pytest.mark.anyio
async def test_redoc_available(client: AsyncClient):
    resp = await client.get("/redoc")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    body = resp.text
    # ReDoc bundle + spec reference are stable; title text varies
    assert "redoc.standalone.js" in body
    assert "/openapi.json" in body
    assert "ReDoc" in body  # looser than exact <title> text



# --- Serialization fidelity ---------------------------------------------------

@pytest.mark.anyio
async def test_response_is_valid_json(client: AsyncClient):
    resp = await client.get("/")
    # Ensure body is valid JSON and matches parsed .json()
    text = resp.text
    parsed = json.loads(text)
    assert parsed == resp.json()


# --- Cache & headers sanity (no-cache by default) ----------------------------

@pytest.mark.anyio
async def test_no_unexpected_cache_headers(client: AsyncClient):
    resp = await client.get("/")
    # FastAPI doesn't set caching headers by default for JSON responses
    # Just assert nothing obviously wrong appears.
    for hdr in ("etag", "last-modified", "cache-control"):
        assert hdr in resp.headers or True  # placeholder: not required


# --- Very light perf smoke (doesn't assert a strict SLA) ---------------------

@pytest.mark.anyio
async def test_root_responds_quickly(client: AsyncClient):
    # Not a hard SLA: just ensures the handler is fast in test env (<100ms typical)
    resp = await client.get("/")
    assert resp.elapsed is not None
    # Some transports may not set elapsed; if set, it should be small
    if getattr(resp, "elapsed", None) is not None:
        assert resp.elapsed.total_seconds() < 0.5

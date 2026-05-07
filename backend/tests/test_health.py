def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] in {"ok", "error"}
    assert "version" in body


def test_health_response_has_request_id(client):
    response = client.get("/health")
    assert "X-Request-ID" in response.headers


def test_unknown_route_returns_standard_error(client):
    response = client.get("/no-such-route")
    assert response.status_code == 404
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"

"""
Integration tests — authentication flow.

Covers: login, token validation, logout, revoked token rejection.
"""

import pytest

from tests.integration.conftest import PASSWORD, auth


class TestLogin:
    def test_success_returns_access_token(self, client):
        resp = client.post("/api/auth/login", json={
            "identifier": "integration_user_a",
            "password": PASSWORD,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert isinstance(body["access_token"], str)
        assert len(body["access_token"]) > 20

    def test_wrong_password_returns_401(self, client):
        resp = client.post("/api/auth/login", json={
            "identifier": "integration_user_a",
            "password": "wrong-password",
        })
        assert resp.status_code == 401

    def test_unknown_user_returns_401(self, client):
        resp = client.post("/api/auth/login", json={
            "identifier": "no_such_user_xyz",
            "password": PASSWORD,
        })
        assert resp.status_code == 401

    def test_missing_fields_returns_422(self, client):
        resp = client.post("/api/auth/login", json={"identifier": "integration_user_a"})
        assert resp.status_code == 422


class TestMe:
    def test_without_token_returns_401(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_with_valid_token_returns_user_info(self, client, token_a):
        resp = client.get("/api/auth/me", headers=auth(token_a))
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "integration_user_a"

    def test_with_malformed_token_returns_401(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.token"})
        assert resp.status_code == 401


class TestLogout:
    def test_logout_then_token_rejected(self, client):
        # Get a fresh token (separate from module-scoped token_a)
        login_resp = client.post("/api/auth/login", json={
            "identifier": "integration_user_b",
            "password": PASSWORD,
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # Token works before logout
        me_before = client.get("/api/auth/me", headers=auth(token))
        assert me_before.status_code == 200

        # Logout
        logout_resp = client.post("/api/auth/logout", headers=auth(token))
        assert logout_resp.status_code == 204

        # Same token must now be rejected
        me_after = client.get("/api/auth/me", headers=auth(token))
        assert me_after.status_code == 401

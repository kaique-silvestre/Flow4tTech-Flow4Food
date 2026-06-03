"""
Integration tests — Row Level Security (tenant isolation).

Verifies that RLS policies correctly isolate data between tenants.
Uses the `categorias` endpoint as a representative tenant-scoped resource.

Key invariant: a request authenticated as Tenant A must NEVER see or modify
data belonging to Tenant B, even though both rows exist in the same table.
"""

import pytest
from sqlalchemy import text

from tests.integration.conftest import TENANT_A, TENANT_B, auth


@pytest.fixture(scope="module", autouse=True)
def seed_categorias(db):
    """Insert one categoria per tenant directly (bypasses RLS as superuser)."""
    db.execute(text(
        "INSERT INTO categorias (tenant_id, nome, ativo) "
        "VALUES (:ta, 'Categoria Tenant A', true), (:tb, 'Categoria Tenant B', true) "
        "ON CONFLICT DO NOTHING"
    ), {"ta": TENANT_A, "tb": TENANT_B})
    db.commit()
    # No explicit cleanup — seed_tenants in conftest deletes all categorias for these tenants


class TestCategoriaIsolation:
    def test_tenant_a_sees_only_own_categorias(self, client, token_a):
        resp = client.get("/api/categorias", headers=auth(token_a))
        assert resp.status_code == 200
        nomes = [c["nome"] for c in resp.json()]
        assert "Categoria Tenant A" in nomes
        assert "Categoria Tenant B" not in nomes

    def test_tenant_b_sees_only_own_categorias(self, client, token_b):
        resp = client.get("/api/categorias", headers=auth(token_b))
        assert resp.status_code == 200
        nomes = [c["nome"] for c in resp.json()]
        assert "Categoria Tenant B" in nomes
        assert "Categoria Tenant A" not in nomes

    def test_tenant_a_cannot_update_tenant_b_categoria(self, client, token_a, db):
        # Get Tenant B's categoria ID directly (superuser, bypasses RLS)
        row = db.execute(text(
            "SELECT id FROM categorias WHERE tenant_id = :tb AND nome = 'Categoria Tenant B' LIMIT 1"
        ), {"tb": TENANT_B}).fetchone()
        assert row is not None, "Categoria Tenant B not found in DB"
        cat_b_id = row[0]

        # Tenant A tries to update Tenant B's row — must return 404 (not visible through RLS)
        resp = client.put(
            f"/api/categorias/{cat_b_id}",
            json={"nome": "Hijacked by Tenant A"},
            headers=auth(token_a),
        )
        assert resp.status_code == 404

    def test_tenant_a_cannot_delete_tenant_b_categoria(self, client, token_a, db):
        row = db.execute(text(
            "SELECT id FROM categorias WHERE tenant_id = :tb AND nome = 'Categoria Tenant B' LIMIT 1"
        ), {"tb": TENANT_B}).fetchone()
        assert row is not None
        cat_b_id = row[0]

        resp = client.delete(f"/api/categorias/{cat_b_id}", headers=auth(token_a))
        assert resp.status_code == 404

        # Row must still exist in DB (was not deleted)
        still_exists = db.execute(text(
            "SELECT id FROM categorias WHERE id = :id"
        ), {"id": cat_b_id}).fetchone()
        assert still_exists is not None


class TestCategoriasCrud:
    def test_create_and_list(self, client, token_a):
        # Create
        resp = client.post("/api/categorias", json={"nome": "Nova Categoria A"}, headers=auth(token_a))
        assert resp.status_code == 201
        body = resp.json()
        assert body["nome"] == "Nova Categoria A"
        cat_id = body["id"]

        # Appears in list
        list_resp = client.get("/api/categorias", headers=auth(token_a))
        assert list_resp.status_code == 200
        ids = [c["id"] for c in list_resp.json()]
        assert cat_id in ids

    def test_created_row_not_visible_to_other_tenant(self, client, token_a, token_b):
        # Tenant A creates a categoria
        resp = client.post(
            "/api/categorias",
            json={"nome": "Exclusive to Tenant A"},
            headers=auth(token_a),
        )
        assert resp.status_code == 201
        cat_id = resp.json()["id"]

        # Tenant B cannot see it
        list_resp = client.get("/api/categorias", headers=auth(token_b))
        ids = [c["id"] for c in list_resp.json()]
        assert cat_id not in ids

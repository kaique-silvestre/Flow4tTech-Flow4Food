"""
Integration test — tenant context propagation under real concurrency.

Regression test for the critical audit finding: `_tenant_ctx` (backing the
per-request RLS SET ROLE / SET app.tenant_id) must be scoped per-request, not
per-OS-thread. `categorias_repository.create()` does `db.commit()` followed
by `db.refresh(obj)` — commit releases the connection back to the pool, and
refresh() checks a new one back out, which re-triggers the SQLAlchemy pool
"checkout" listener in `core/database.py`. That listener re-applies
SET ROLE / SET app.tenant_id based on whatever the current tenant context
holds.

If tenant context leaked between concurrent requests sharing anyio's
threadpool (the threading.local bug this test guards against), the
checkout listener would sometimes apply the WRONG tenant's RLS context
to a request's connection. Since `categorias.tenant_id` has a
`current_setting('app.tenant_id')` server default applied at INSERT time
(before any leak could occur) but RLS filters `db.refresh()`'s SELECT by
the (possibly wrong, leaked) app.tenant_id, a leak manifests as a very
concrete symptom: refresh() finds 0 rows for the just-inserted row and
raises, turning the request into an HTTP 500 instead of 201 — or, in the
worst case, the row silently gets attributed to the wrong tenant.

This test fires many concurrent create requests, alternating between two
tenants, via real threads hitting a shared TestClient (real ASGI app, real
worker threadpool) — and asserts every request succeeds and every created
row is attributed to the tenant that created it, with zero cross-tenant
leakage.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from sqlalchemy import text

from tests.integration.conftest import TENANT_A, TENANT_B, auth

N_ROUNDS = 30  # requests per tenant — interleaved, run concurrently


@pytest.fixture(autouse=True)
def cleanup_created(db):
    """Track and clean up categorias created by this module's tests."""
    yield
    db.execute(text(
        "DELETE FROM categorias WHERE tenant_id IN (:a, :b) AND nome LIKE 'ConcurrencyTest_%'"
    ), {"a": TENANT_A, "b": TENANT_B})
    db.commit()


class TestTenantContextConcurrency:
    def test_concurrent_creates_never_leak_tenant_context(self, client, token_a, token_b, db):
        run_id = uuid.uuid4().hex[:8]

        def create(tenant_label: str, token: str, i: int):
            nome = f"ConcurrencyTest_{run_id}_{tenant_label}_{i}"
            resp = client.post(
                "/api/categorias",
                json={"nome": nome},
                headers=auth(token),
            )
            return tenant_label, nome, resp

        jobs = []
        for i in range(N_ROUNDS):
            jobs.append(("A", token_a, i))
            jobs.append(("B", token_b, i))

        results = []
        with ThreadPoolExecutor(max_workers=16) as pool:
            futures = [pool.submit(create, label, token, i) for label, token, i in jobs]
            for fut in as_completed(futures):
                results.append(fut.result())

        assert len(results) == len(jobs)

        # 1. Every request must succeed — a leaked/wrong tenant context on the
        #    refresh() after commit() would surface as a non-201 (typically 500).
        failures = [(label, nome, resp.status_code, resp.text) for label, nome, resp in results if resp.status_code != 201]
        assert not failures, f"Some creates failed (possible tenant context leak): {failures}"

        # 2. The API response body itself must never carry the wrong data —
        #    i.e. no response returned a name belonging to the other tenant's job.
        for label, nome, resp in results:
            body = resp.json()
            assert body["nome"] == nome

        # 3. Ground truth: query the DB directly (bypasses API/RLS) and verify
        #    every created row's tenant_id matches the tenant that created it.
        rows = db.execute(text(
            "SELECT nome, tenant_id FROM categorias WHERE nome LIKE :pattern"
        ), {"pattern": f"ConcurrencyTest_{run_id}_%"}).fetchall()
        rows_by_name = {r[0]: r[1] for r in rows}
        assert len(rows_by_name) == len(jobs), "Some created rows are missing from the DB"

        for label, nome, _resp in results:
            expected_tenant = TENANT_A if label == "A" else TENANT_B
            assert rows_by_name[nome] == expected_tenant, (
                f"Row {nome!r} was created under tenant {rows_by_name[nome]}, "
                f"expected {expected_tenant} (tenant context leaked across requests)"
            )

        # 4. Each tenant's list endpoint shows only its own rows for this run —
        #    no cross-tenant visibility leak either.
        list_a = client.get("/api/categorias", headers=auth(token_a)).json()
        list_b = client.get("/api/categorias", headers=auth(token_b)).json()
        names_a = {c["nome"] for c in list_a if c["nome"].startswith(f"ConcurrencyTest_{run_id}_")}
        names_b = {c["nome"] for c in list_b if c["nome"].startswith(f"ConcurrencyTest_{run_id}_")}

        expected_a = {f"ConcurrencyTest_{run_id}_A_{i}" for i in range(N_ROUNDS)}
        expected_b = {f"ConcurrencyTest_{run_id}_B_{i}" for i in range(N_ROUNDS)}

        assert names_a == expected_a
        assert names_b == expected_b
        assert names_a.isdisjoint(names_b)

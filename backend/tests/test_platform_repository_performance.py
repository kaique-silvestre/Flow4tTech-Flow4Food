from unittest.mock import MagicMock
from types import SimpleNamespace

from src.repositories import platform_repository
from src.services import tenant_service


def test_cockpit_uses_indexable_month_range_and_pagination():
    db = MagicMock()
    db.execute.side_effect = [MagicMock(scalar_one=lambda: 2), MagicMock(all=lambda: [])]

    result = platform_repository.get_cockpit_metrics(db, status_filter="ativa", page=2, page_size=25)

    assert result == {"items": [], "total": 2, "page": 2, "page_size": 25, "total_pages": 1}
    query = str(db.execute.call_args_list[1].args[0])
    assert "created_at >= :month_start" in query
    assert "created_at < :month_end" in query
    assert "DATE_TRUNC('month', c.created_at)" not in query
    assert "ORDER BY t.id LIMIT :limit OFFSET :offset" in query
    assert "LIMIT :limit OFFSET :offset" in query
    assert db.execute.call_args_list[1].args[1]["offset"] == 25


def test_get_tenant_profiles_batches_permissions_and_user_counts():
    db = MagicMock()
    profiles = [
        SimpleNamespace(id=10, name="Admin", description=None, is_active=True),
        SimpleNamespace(id=11, name="Caixa", description="", is_active=True),
    ]
    db.execute.side_effect = [
        MagicMock(scalars=lambda: MagicMock(all=lambda: profiles)),
        MagicMock(all=lambda: [MagicMock(profile_id=10, screen="dashboard")]),
        MagicMock(all=lambda: [MagicMock(profile_id=10, user_count=3), MagicMock(profile_id=11, user_count=1)]),
    ]

    result = platform_repository.get_tenant_profiles(db, tenant_id=7)

    assert db.execute.call_count == 3
    assert result == [
        {"id": 10, "name": "Admin", "description": None, "is_active": True, "permissions": ["dashboard"], "user_count": 3},
        {"id": 11, "name": "Caixa", "description": "", "is_active": True, "permissions": [], "user_count": 1},
    ]


def test_legacy_tenant_listing_uses_one_batched_subscription_lookup(monkeypatch):
    tenant = MagicMock(id=3)
    subscription = MagicMock()
    batched_lookup = MagicMock(return_value=[(tenant, subscription)])
    monkeypatch.setattr(tenant_service, "list_tenants_with_assinaturas", batched_lookup)
    monkeypatch.setattr(tenant_service, "_to_response", lambda current, assinatura: (current, assinatura))

    assert tenant_service.get_all_tenants(MagicMock()) == [(tenant, subscription)]
    batched_lookup.assert_called_once()

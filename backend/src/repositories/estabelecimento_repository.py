from typing import Optional

from sqlalchemy.orm import Session

from src.models.tenants import Tenant
from src.repositories.tenant_repository import get_tenant_by_id


def get_estabelecimento(db: Session, tenant_id: int) -> Optional[Tenant]:
    return get_tenant_by_id(db, tenant_id)


def upsert_estabelecimento(
    db: Session,
    tenant_id: int,
    nome: Optional[str] = None,
    cnpj: Optional[str] = None,
    endereco: Optional[str] = None,
    telefone: Optional[str] = None,
) -> Tenant:
    tenant = get_tenant_by_id(db, tenant_id)
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id} não encontrado")
    if nome is not None:
        tenant.nome_fantasia = nome
    if cnpj is not None:
        tenant.cnpj = cnpj
    if endereco is not None:
        tenant.endereco = endereco
    if telefone is not None:
        tenant.telefone = telefone
    db.commit()
    db.refresh(tenant)
    return tenant

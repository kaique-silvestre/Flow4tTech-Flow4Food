"""Match NF-e parsed data against DB records. Read-only."""

import unicodedata
from typing import Optional

from sqlalchemy.orm import Session

from src.models.insumos import Insumo
from src.repositories import fornecedores_repository, insumos_repository
from src.schemas.nfe import NFeImportResponse, NFeItemResponse
from src.services.nfe_parser import NFeData, NFeItem


def _normalize(text: str) -> str:
    """Lowercase + strip accents for fuzzy name comparison."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def _build_insumo_index(db: Session) -> tuple[dict[str, Insumo], dict[str, Insumo]]:
    """Load every active insumo once and index it for in-memory matching.

    Replaces per-item DB lookups (both the EAN point query and the full
    active-insumos scan) with a single query reused across every item of
    the NF-e, and a single unbounded query (no 2000-row cap) so tenants
    with more active insumos than any pagination limit are not silently
    truncated.
    """
    by_ean: dict[str, Insumo] = {}
    by_name: dict[str, Insumo] = {}
    for insumo in insumos_repository.list_all_ativos(db):
        if insumo.ean and insumo.ean not in by_ean:
            by_ean[insumo.ean] = insumo
        normalized = _normalize(insumo.nome)
        if normalized not in by_name:
            by_name[normalized] = insumo
    return by_ean, by_name


def _match_insumo(
    item: NFeItem, by_ean: dict[str, Insumo], by_name: dict[str, Insumo]
) -> Optional[Insumo]:
    # 1. EAN exact match
    if item.ean and item.ean in by_ean:
        return by_ean[item.ean]

    # 2. Name case-insensitive + accent-stripped match
    return by_name.get(_normalize(item.nome))


def match_nfe(db: Session, data: NFeData) -> NFeImportResponse:
    # Fornecedor match by CNPJ
    fornecedor = fornecedores_repository.get_by_cnpj(db, data.cnpj_emitente)
    fornecedor_id: Optional[int] = fornecedor.id if fornecedor else None

    by_ean, by_name = _build_insumo_index(db) if data.itens else ({}, {})

    itens: list[NFeItemResponse] = []
    for item in data.itens:
        matched = _match_insumo(item, by_ean, by_name)
        itens.append(NFeItemResponse(
            nome_xml=item.nome,
            ean_xml=item.ean,
            quantidade=item.quantidade,
            unidade_xml=item.unidade_xml,
            custo_unitario=item.custo_unitario,
            custo_total=item.custo_total,
            insumo_id=matched.id if matched else None,
            insumo_nome=matched.nome if matched else None,
        ))

    return NFeImportResponse(
        numero_nota=data.numero_nota,
        data_compra=data.data_emissao,
        cnpj_xml=data.cnpj_emitente,
        fornecedor_id=fornecedor_id,
        fornecedor_nome_xml=data.nome_emitente,
        itens=itens,
    )

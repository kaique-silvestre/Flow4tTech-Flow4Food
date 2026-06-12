"""Match NF-e parsed data against DB records. Read-only."""

import unicodedata
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.insumos import Insumo
from src.repositories import fornecedores_repository, insumos_repository
from src.schemas.nfe import NFeImportResponse, NFeItemResponse
from src.services.nfe_parser import NFeData, NFeItem


def _normalize(text: str) -> str:
    """Lowercase + strip accents for fuzzy name comparison."""
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip()


def _match_insumo(db: Session, item: NFeItem) -> Optional[Insumo]:
    # 1. EAN exact match
    if item.ean:
        found = insumos_repository.get_by_ean(db, item.ean)
        if found:
            return found

    # 2. Name case-insensitive + accent-stripped match
    normalized_xml = _normalize(item.nome)
    all_insumos, _ = insumos_repository.list_ativos(db, por_pagina=2000)
    for insumo in all_insumos:
        if _normalize(insumo.nome) == normalized_xml:
            return insumo

    return None


def match_nfe(db: Session, data: NFeData) -> NFeImportResponse:
    # Fornecedor match by CNPJ
    fornecedor = fornecedores_repository.get_by_cnpj(db, data.cnpj_emitente)
    fornecedor_id: Optional[int] = fornecedor.id if fornecedor else None

    itens: list[NFeItemResponse] = []
    for item in data.itens:
        matched = _match_insumo(db, item)
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

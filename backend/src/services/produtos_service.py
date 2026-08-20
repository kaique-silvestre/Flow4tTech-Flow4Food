import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.ficha_tecnica import FichaTecnica
from src.models.insumos import Insumo
from src.models.promocoes import Promocao, PromocaoProduto
from src.repositories import insumos_repository, produtos_repository
from src.schemas.produtos import (
    FichaTecnicaItemResponse,
    ProdutoCreateRequest,
    ProdutoPageResponse,
    ProdutoResponse,
    ProdutoUpdateRequest,
)


def _resolve_promos_batch(db: Session, produto_ids: list[int]) -> dict[int, Promocao]:
    """Batched equivalent of comandas_service.resolve_promo for many produto_ids at once."""
    if not produto_ids:
        return {}

    hoje = datetime.date.today()
    hora_agora = datetime.datetime.now().time()
    rows = db.execute(
        select(Promocao, PromocaoProduto.produto_id)
        .join(PromocaoProduto, PromocaoProduto.promocao_id == Promocao.id)
        .where(
            PromocaoProduto.produto_id.in_(produto_ids),
            Promocao.ativo == True,  # noqa: E712
            Promocao.data_inicio <= hoje,
            (Promocao.data_fim == None) | (Promocao.data_fim >= hoje),  # noqa: E711
            Promocao.hora_inicio <= hora_agora,
            Promocao.hora_fim >= hora_agora,
        )
        .order_by(Promocao.id)
    ).all()

    promos_by_produto: dict[int, list[Promocao]] = {}
    for promo, produto_id in rows:
        promos_by_produto.setdefault(produto_id, []).append(promo)

    # Python weekday: 0=Mon…6=Sun; issue spec: 0=Sun…6=Sat
    _weekday_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
    dia_semana_spec = _weekday_map[hoje.weekday()]
    dia_mes = hoje.day

    result: dict[int, Promocao] = {}
    for produto_id, promos in promos_by_produto.items():
        for promo in promos:
            if promo.recorrencia == "semanal":
                dias = promo.dias_semana or []
                if isinstance(dias, str):
                    import json as _json
                    dias = _json.loads(dias)
                if dia_semana_spec not in dias:
                    continue
            elif promo.recorrencia == "mensal":
                dias = promo.dias_mes or []
                if isinstance(dias, str):
                    import json as _json
                    dias = _json.loads(dias)
                if dia_mes not in dias:
                    continue
            result[produto_id] = promo
            break
    return result


def _build_responses(db: Session, produtos: list) -> list[ProdutoResponse]:
    """Builds ProdutoResponse objects for a batch of produtos with a fixed number of
    queries total (ficha técnica, insumos, promoções), regardless of how many produtos
    are passed in — avoids the N+1 pattern of querying per product."""
    from decimal import Decimal as D

    from src.services.comandas_service import apply_discount

    if not produtos:
        return []

    produto_ids = [p.id for p in produtos]

    componentes = db.execute(
        select(FichaTecnica).where(FichaTecnica.produto_id.in_(produto_ids))
    ).scalars().all()
    componentes_by_produto: dict[int, list[FichaTecnica]] = {}
    for comp in componentes:
        componentes_by_produto.setdefault(comp.produto_id, []).append(comp)

    insumo_ids = {comp.insumo_id for comp in componentes}
    insumos_by_id: dict[int, Insumo] = {}
    if insumo_ids:
        insumos_by_id = {
            insumo.id: insumo
            for insumo in db.execute(select(Insumo).where(Insumo.id.in_(insumo_ids))).scalars().all()
        }

    promo_by_produto = _resolve_promos_batch(db, produto_ids)

    responses: list[ProdutoResponse] = []
    for produto in produtos:
        componentes_p = componentes_by_produto.get(produto.id, [])
        ficha_resp = None
        producao_possivel: Optional[int] = None
        if componentes_p:
            ficha_resp = []
            minimos: list[int] = []
            for comp in componentes_p:
                insumo = insumos_by_id.get(comp.insumo_id)
                ficha_resp.append(FichaTecnicaItemResponse(
                    insumo_id=comp.insumo_id,
                    insumo_nome=insumo.nome if insumo else f"Insumo {comp.insumo_id}",
                    quantidade=comp.quantidade,
                    unidade_base=insumo.unidade_base if insumo else "un",
                    custo_medio_insumo=insumo.custo_medio if insumo else None,
                ))
                if insumo is None or comp.quantidade <= 0:
                    minimos.append(0)
                else:
                    disponivel = insumo.estoque_atual - insumo.estoque_reservado
                    if disponivel <= D("0"):
                        minimos.append(0)
                    else:
                        minimos.append(int(disponivel // comp.quantidade))
            producao_possivel = min(minimos) if minimos else 0

        preco_promocional = None
        nome_promocao = None
        if produto.preco_venda is not None:
            promo = promo_by_produto.get(produto.id)
            if promo:
                preco_promocional = apply_discount(D(str(produto.preco_venda)), promo)
                nome_promocao = promo.nome

        responses.append(ProdutoResponse(
            id=produto.id,
            nome=produto.nome,
            categoria_id=produto.categoria_id,
            preco_venda=produto.preco_venda,
            ativo=produto.ativo,
            ficha_tecnica=ficha_resp,
            producao_possivel=producao_possivel,
            preco_promocional=preco_promocional,
            nome_promocao=nome_promocao,
        ))
    return responses


def _build_response(db: Session, produto) -> ProdutoResponse:
    return _build_responses(db, [produto])[0]


def list_produtos(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
    ativo: Optional[bool] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> ProdutoPageResponse:
    items, total = produtos_repository.list_ativos(db, categoria_id, busca, ativo=ativo, pagina=pagina, por_pagina=por_pagina)
    import math
    return ProdutoPageResponse(
        itens=_build_responses(db, items),
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


def get_produto(db: Session, produto_id: int) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    return _build_response(db, obj)


def create_produto(db: Session, data: ProdutoCreateRequest) -> ProdutoResponse:
    if data.ficha_tecnica:
        for comp in data.ficha_tecnica:
            insumo = insumos_repository.get_by_id(db, comp.insumo_id)
            if insumo is None:
                raise AppError(
                    ErrorCode.NOT_FOUND,
                    f"Insumo id={comp.insumo_id} não encontrado",
                    http_status=404,
                )

    obj = produtos_repository.create(db, data)
    if data.ficha_tecnica:
        produtos_repository.upsert_ficha(db, obj.id, data.ficha_tecnica)
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def update_produto(db: Session, produto_id: int, data: ProdutoUpdateRequest) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)

    if data.ficha_tecnica:
        for comp in data.ficha_tecnica:
            insumo = insumos_repository.get_by_id(db, comp.insumo_id)
            if insumo is None:
                raise AppError(
                    ErrorCode.NOT_FOUND,
                    f"Insumo id={comp.insumo_id} não encontrado",
                    http_status=404,
                )

    obj = produtos_repository.update(db, produto_id, data)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    produtos_repository.upsert_ficha(db, produto_id, data.ficha_tecnica or [])
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def delete_produto(db: Session, produto_id: int) -> None:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    if produtos_repository.is_referenced_in_comanda(db, produto_id):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Produto tem histórico em comandas e não pode ser excluído. Use 'Desativar'.",
            http_status=422,
        )
    db.delete(obj)
    db.commit()


def desativar_produto(db: Session, produto_id: int) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    obj.ativo = False
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def reativar_produto(db: Session, produto_id: int) -> ProdutoResponse:
    obj = produtos_repository.get_by_id(db, produto_id)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado", http_status=404)
    obj.ativo = True
    db.commit()
    db.refresh(obj)
    return _build_response(db, obj)


def get_top_produtos(db: Session, dias: int, limit: int) -> list[ProdutoResponse]:
    import datetime

    from sqlalchemy import func

    from src.models.itens_comanda import ItemComanda

    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=dias)
    rows = db.execute(
        select(ItemComanda.produto_id, func.count(ItemComanda.id).label("cnt"))
        .where(
            ItemComanda.cancelado == False,  # noqa: E712
            ItemComanda.created_at >= cutoff,
        )
        .group_by(ItemComanda.produto_id)
        .order_by(func.count(ItemComanda.id).desc())
        .limit(limit)
    ).all()

    result = []
    for produto_id, _cnt in rows:
        obj = produtos_repository.get_by_id(db, produto_id)
        if obj and obj.ativo:
            result.append(_build_response(db, obj))
    return result

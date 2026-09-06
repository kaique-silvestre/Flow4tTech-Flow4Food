import datetime
import json
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.core.logging import get_logger
from src.models.comandas import Comanda, StatusComanda
from src.models.comissoes_garcom import ComissaoGarcom
from src.models.eventos_comanda import TipoEvento
from src.models.garcons import Garcom
from src.models.insumos import Insumo
from src.models.itens_comanda import ItemComanda
from src.models.metodos_pagamento import MetodoPagamento
from src.models.movimentos_estoque import TipoMovimento
from src.models.pagamentos import Pagamento
from src.models.produtos import Produto
from src.models.promocoes import Promocao, PromocaoProduto
from src.repositories import (
    comandas_repository,
    estoque_repository,
    garcons_repository,
    pagamentos_repository,
)
from src.schemas.comandas import (
    CancelarComandaRequest,
    CancelarItemRequest,
    ComandaCreateRequest,
    ComandaResponse,
    EditarItemRequest,
    ItemComandaResponse,
    LancarItemRequest,
    PatchComandaRequest,
    ReabrirComandaRequest,
)
from src.schemas.fechamento import AplicarDescontoRequest, FecharComandaRequest, PagamentoResponse
from src.schemas.produtos import ProdutoResponse
from src.services import produtos_service

logger = get_logger(__name__)

# Taxa de serviço/comissão do garçom aplicada no fechamento de comanda quando
# `taxa_servico=True` — usada tanto para calcular o total esperado de
# pagamento quanto para o valor da comissão gerada.
TAXA_SERVICO_PERCENTUAL = Decimal("10.00")
_TAXA_SERVICO_MULTIPLICADOR = Decimal("1") + TAXA_SERVICO_PERCENTUAL / Decimal("100")


def _parse_pessoas(pessoas_json: Optional[str]) -> list[str]:
    if not pessoas_json:
        return []
    try:
        return json.loads(pessoas_json)
    except (json.JSONDecodeError, TypeError):
        # Não loga o valor bruto de `pessoas_json` — pode conter nome/telefone
        # de cliente. Só metadados não-sensíveis (tamanho da string).
        logger.warning("comanda_pessoas_parse_failed", pessoas_json_length=len(str(pessoas_json)))
        return []


def resolve_promo(db: Session, produto_id: int) -> Optional[Promocao]:
    hoje = datetime.date.today()
    hora_agora = datetime.datetime.now().time()
    promos = (
        db.execute(
            select(Promocao)
            .join(PromocaoProduto, PromocaoProduto.promocao_id == Promocao.id)
            .where(
                PromocaoProduto.produto_id == produto_id,
                Promocao.ativo == True,  # noqa: E712
                Promocao.data_inicio <= hoje,
                (Promocao.data_fim == None) | (Promocao.data_fim >= hoje),  # noqa: E711
                Promocao.hora_inicio <= hora_agora,
                Promocao.hora_fim >= hora_agora,
            )
            .order_by(Promocao.id)
        )
        .scalars()
        .all()
    )
    # Python weekday: 0=Mon…6=Sun; issue spec: 0=Sun…6=Sat
    _weekday_map = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
    dia_semana_spec = _weekday_map[hoje.weekday()]
    dia_mes = hoje.day

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
        return promo
    return None


def apply_discount(preco_venda: Decimal, promo: Promocao) -> Decimal:
    valor = Decimal(str(promo.valor_desconto))
    if promo.tipo_desconto == "porcentagem":
        resultado = preco_venda * (1 - valor / Decimal("100"))
    else:
        resultado = preco_venda - valor
    return max(Decimal("0"), resultado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _build_item_response(
    ic: ItemComanda,
    produtos_by_id: dict[int, Produto],
    promos_by_id: dict[int, Promocao],
) -> ItemComandaResponse:
    produto = produtos_by_id.get(ic.produto_id)
    item_nome = produto.nome if produto else f"Produto {ic.produto_id}"
    subtotal = ic.quantidade * ic.preco_unitario
    promocao_nome: Optional[str] = None
    if ic.promocao_id:
        promo = promos_by_id.get(ic.promocao_id)
        promocao_nome = promo.nome if promo else None
    return ItemComandaResponse(
        id=ic.id,
        item_id=ic.produto_id,
        item_nome=item_nome,
        quantidade=ic.quantidade,
        preco_unitario=ic.preco_unitario,
        subtotal=subtotal,
        pessoa_associada=ic.pessoa_associada,
        observacao=ic.observacao,
        cortesia=ic.cortesia,
        cancelado=ic.cancelado,
        motivo_cancelamento=ic.motivo_cancelamento,
        estornado=ic.estornado,
        created_at=ic.created_at,
        promocao_id=ic.promocao_id,
        promocao_nome=promocao_nome,
    )


def _build_responses(db: Session, comandas: list[Comanda]) -> list[ComandaResponse]:
    """Builds ComandaResponse objects for a batch of comandas with a fixed number of
    queries total (garçons, itens, produtos, promoções, pagamentos, métodos), regardless
    of how many comandas are passed in — avoids the N+1 pattern of querying per comanda."""
    if not comandas:
        return []

    comanda_ids = [c.id for c in comandas]

    garcom_ids = {c.garcom_id for c in comandas}
    garcoes_by_id: dict[int, Garcom] = {
        g.id: g for g in db.execute(select(Garcom).where(Garcom.id.in_(garcom_ids))).scalars().all()
    }

    itens = (
        db.execute(
            select(ItemComanda)
            .where(ItemComanda.comanda_id.in_(comanda_ids))
            .order_by(ItemComanda.created_at.asc())
        )
        .scalars()
        .all()
    )
    itens_by_comanda: dict[int, list[ItemComanda]] = {}
    for ic in itens:
        itens_by_comanda.setdefault(ic.comanda_id, []).append(ic)

    produto_ids = {ic.produto_id for ic in itens}
    produtos_by_id: dict[int, Produto] = (
        {p.id: p for p in db.execute(select(Produto).where(Produto.id.in_(produto_ids))).scalars().all()}
        if produto_ids
        else {}
    )

    promocao_ids = {ic.promocao_id for ic in itens if ic.promocao_id is not None}
    promos_by_id: dict[int, Promocao] = (
        {pr.id: pr for pr in db.execute(select(Promocao).where(Promocao.id.in_(promocao_ids))).scalars().all()}
        if promocao_ids
        else {}
    )

    pagamentos = (
        db.execute(select(Pagamento).where(Pagamento.comanda_id.in_(comanda_ids)).order_by(Pagamento.id))
        .scalars()
        .all()
    )
    pagamentos_by_comanda: dict[int, list[Pagamento]] = {}
    for p in pagamentos:
        pagamentos_by_comanda.setdefault(p.comanda_id, []).append(p)

    metodo_ids = {p.metodo_id for p in pagamentos}
    metodos_by_id: dict[int, MetodoPagamento] = (
        {m.id: m for m in db.execute(select(MetodoPagamento).where(MetodoPagamento.id.in_(metodo_ids))).scalars().all()}
        if metodo_ids
        else {}
    )

    now = datetime.datetime.utcnow()
    responses: list[ComandaResponse] = []
    for comanda in comandas:
        garcom = garcoes_by_id.get(comanda.garcom_id)
        garcom_nome = garcom.nome if garcom else f"Garçom {comanda.garcom_id}"

        pessoas = _parse_pessoas(comanda.pessoas)
        itens_resp = [
            _build_item_response(ic, produtos_by_id, promos_by_id)
            for ic in itens_by_comanda.get(comanda.id, [])
        ]

        total_parcial = sum(
            (ir.subtotal for ir in itens_resp if not ir.cancelado),
            Decimal("0"),
        )

        created = comanda.created_at
        if hasattr(created, "replace"):
            delta = now - created.replace(tzinfo=None)
        else:
            delta = datetime.timedelta(0)
        tempo_aberta_minutos = int(delta.total_seconds() // 60)

        pagamentos_resp = []
        for p in pagamentos_by_comanda.get(comanda.id, []):
            metodo = metodos_by_id.get(p.metodo_id)
            metodo_nome = metodo.nome if metodo else f"Método {p.metodo_id}"
            pagamentos_resp.append(
                PagamentoResponse(
                    id=p.id,
                    metodo_id=p.metodo_id,
                    metodo_nome=metodo_nome,
                    valor=p.valor,
                    valor_nota=p.valor_nota,
                    troco=p.troco,
                )
            )

        responses.append(
            ComandaResponse(
                id=comanda.id,
                numero_dia=comanda.numero_dia,
                identificacao=comanda.identificacao,
                tipo_identificacao=comanda.tipo_identificacao,
                garcom_id=comanda.garcom_id,
                garcom_nome=garcom_nome,
                status=comanda.status,
                version=comanda.version,
                pessoas=pessoas,
                total_parcial=total_parcial,
                itens_ativos=itens_resp,
                created_at=comanda.created_at,
                tempo_aberta_minutos=tempo_aberta_minutos,
                desconto_percentual=comanda.desconto_percentual,
                desconto_valor=comanda.desconto_valor,
                total=comanda.total,
                saldo_pendente=comanda.saldo_pendente,
                data_fechamento=comanda.data_fechamento,
                pagamentos=pagamentos_resp,
            )
        )
    return responses


def _build_response(db: Session, comanda: Comanda) -> ComandaResponse:
    return _build_responses(db, [comanda])[0]


def abrir_comanda(db: Session, data: ComandaCreateRequest) -> ComandaResponse:
    garcom = garcons_repository.get_by_id(db, data.garcom_id)
    if garcom is None:
        raise AppError(ErrorCode.NOT_FOUND, "Garçom não encontrado", http_status=404)
    if not garcom.ativo:
        raise AppError(ErrorCode.GARCOM_INATIVO, "Garçom inativo não pode abrir comanda", http_status=400)

    comanda = comandas_repository.create_comanda(db, data)
    comandas_repository.add_evento(
        db,
        comanda.id,
        TipoEvento.COMANDA_ABERTA,
        {"identificacao": data.identificacao, "garcom_id": data.garcom_id},
        garcom_id=data.garcom_id,
    )
    db.commit()
    db.refresh(comanda)
    logger.info(
        "comanda_aberta",
        comanda_id=comanda.id,
        tenant_id=comanda.tenant_id,
        garcom_id=data.garcom_id,
    )
    return _build_response(db, comanda)


def get_comanda(db: Session, comanda_id: int) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    return _build_response(db, comanda)


def list_comandas_abertas(db: Session, busca: Optional[str] = None) -> list[ComandaResponse]:
    comandas = comandas_repository.list_abertas(db, busca)
    return _build_responses(db, comandas)


def list_comandas_fechadas(
    db: Session,
    busca: Optional[str] = None,
    data_inicio: Optional[datetime.date] = None,
    data_fim: Optional[datetime.date] = None,
) -> list[ComandaResponse]:
    """Filtra comandas fechadas por período. `data_fim` é tratado como
    inclusivo (até o último segundo do dia) — a conversão de `date` pra
    o range de `datetime` usado na query fica aqui, não na camada de route."""
    dt_inicio = datetime.datetime.combine(data_inicio, datetime.time.min) if data_inicio else None
    dt_fim = datetime.datetime.combine(data_fim, datetime.time.max) if data_fim else None
    comandas = comandas_repository.list_fechadas(db, busca, dt_inicio, dt_fim)
    return _build_responses(db, comandas)


_ABERTA_STATUSES = {StatusComanda.ABERTA.value, StatusComanda.REABERTA.value}


def _lock_comanda(db: Session, comanda_id: int, version: int, tenant_id: int) -> None:
    """Optimistic lock: atomically bumps a comanda's version, matching only
    if it's still at `version`. Raises COMANDA_DESATUALIZADA (409) on
    conflict (concurrent mutation/duplicate request). The repository call
    expires all session objects, so any already-loaded `Comanda` instance
    transparently reloads its attributes from the DB on next access."""
    ok = comandas_repository.increment_version(db, comanda_id, version, tenant_id)
    if not ok:
        raise AppError(
            ErrorCode.COMANDA_DESATUALIZADA,
            "Comanda foi alterada por outro usuário, recarregue",
            http_status=409,
        )


def patch_comanda(db: Session, comanda_id: int, data: PatchComandaRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    _lock_comanda(db, comanda_id, data.version, comanda.tenant_id)

    if data.garcom_id is not None:
        garcom = garcons_repository.get_by_id(db, data.garcom_id)
        if garcom is None:
            raise AppError(ErrorCode.NOT_FOUND, "Garçom não encontrado", http_status=404)
        if not garcom.ativo:
            raise AppError(ErrorCode.GARCOM_INATIVO, "Garçom inativo", http_status=400)
        comanda.garcom_id = data.garcom_id

    if data.identificacao is not None:
        comanda.identificacao = data.identificacao

    if data.pessoas is not None:
        comanda.pessoas = json.dumps(data.pessoas, ensure_ascii=False)

    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.COMANDA_EDITADA,
        {
            "identificacao": data.identificacao,
            "garcom_id": data.garcom_id,
        },
    )
    db.commit()
    db.refresh(comanda)
    logger.info(
        "comanda_editada",
        comanda_id=comanda_id,
        tenant_id=comanda.tenant_id,
        garcom_id=data.garcom_id,
    )
    return _build_response(db, comanda)


def lancar_item(db: Session, comanda_id: int, data: LancarItemRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    produto = db.execute(select(Produto).where(Produto.id == data.item_id, Produto.ativo == True)).scalar_one_or_none()  # noqa: E712
    if produto is None:
        raise AppError(ErrorCode.NOT_FOUND, "Produto não encontrado ou inativo", http_status=404)

    preco_unitario = Decimal("0") if data.cortesia else (produto.preco_venda or Decimal("0"))
    promocao_id: Optional[int] = None
    if not data.cortesia:
        promo = resolve_promo(db, produto.id)
        if promo:
            preco_unitario = apply_discount(preco_unitario, promo)
            promocao_id = promo.id

    ok = comandas_repository.increment_version(db, comanda_id, data.version, comanda.tenant_id)
    if not ok:
        raise AppError(
            ErrorCode.COMANDA_DESATUALIZADA,
            "Comanda foi alterada por outro usuário, recarregue",
            http_status=409,
        )

    comandas_repository.add_item(
        db,
        comanda_id,
        data.item_id,
        data.quantidade,
        preco_unitario,
        data.pessoa_associada,
        data.observacao,
        data.cortesia,
        promocao_id=promocao_id,
    )
    insuficientes = _reservar_estoque(db, data.item_id, data.quantidade)
    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.ITEM_LANCADO,
        {
            "item_id": data.item_id,
            "quantidade": str(data.quantidade),
            "cortesia": data.cortesia,
            "pessoa_associada": data.pessoa_associada,
            "promocao_id": promocao_id,
        },
    )
    db.commit()
    comanda = comandas_repository.get_by_id(db, comanda_id)
    log_kwargs = {
        "comanda_id": comanda_id,
        "tenant_id": comanda.tenant_id if comanda else None,  # type: ignore[union-attr]
        "item_id": data.item_id,
        "quantidade": str(data.quantidade),
    }
    logger.info("comanda_item_lancado", **log_kwargs)
    if insuficientes:
        logger.warning("comanda_item_lancado_estoque_insuficiente", insumos=insuficientes, **log_kwargs)
    response = _build_response(db, comanda)  # type: ignore[arg-type]
    response.estoque_insuficiente = insuficientes
    return response


def editar_item(
    db: Session,
    comanda_id: int,
    item_comanda_id: int,
    data: EditarItemRequest,
) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    item_c = comandas_repository.get_item(db, item_comanda_id)
    if item_c is None or item_c.comanda_id != comanda_id:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado nesta comanda", http_status=404)
    if item_c.cancelado:
        raise AppError(ErrorCode.CONFLICT, "Item já cancelado", http_status=409)

    ok = comandas_repository.increment_version(db, comanda_id, data.version, comanda.tenant_id)
    if not ok:
        raise AppError(
            ErrorCode.COMANDA_DESATUALIZADA,
            "Comanda foi alterada por outro usuário, recarregue",
            http_status=409,
        )

    qtd_antiga = item_c.quantidade
    qtd_nova = data.quantidade if data.quantidade is not None else qtd_antiga

    insuficientes: list[str] = []
    if qtd_nova != qtd_antiga:
        _liberar_reserva_estoque(db, item_c.produto_id, qtd_antiga)
        insuficientes = _reservar_estoque(db, item_c.produto_id, qtd_nova)

    comandas_repository.update_item(db, item_comanda_id, data.quantidade, data.pessoa_associada, data.observacao)
    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.ITEM_EDITADO,
        {
            "item_comanda_id": item_comanda_id,
            "quantidade": str(data.quantidade) if data.quantidade else None,
            "pessoa_associada": data.pessoa_associada,
            "observacao": data.observacao,
        },
    )
    db.commit()
    comanda = comandas_repository.get_by_id(db, comanda_id)
    log_kwargs = {
        "comanda_id": comanda_id,
        "tenant_id": comanda.tenant_id if comanda else None,  # type: ignore[union-attr]
        "item_comanda_id": item_comanda_id,
    }
    logger.info("comanda_item_editado", **log_kwargs)
    if insuficientes:
        logger.warning("comanda_item_editado_estoque_insuficiente", insumos=insuficientes, **log_kwargs)
    response = _build_response(db, comanda)  # type: ignore[arg-type]
    response.estoque_insuficiente = insuficientes
    return response


def cancelar_item(
    db: Session,
    comanda_id: int,
    item_comanda_id: int,
    data: CancelarItemRequest,
) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    item_c = comandas_repository.get_item(db, item_comanda_id)
    if item_c is None or item_c.comanda_id != comanda_id:
        raise AppError(ErrorCode.NOT_FOUND, "Item não encontrado nesta comanda", http_status=404)
    if item_c.cancelado:
        raise AppError(ErrorCode.CONFLICT, "Item já cancelado", http_status=409)

    ok = comandas_repository.increment_version(db, comanda_id, data.version, comanda.tenant_id)
    if not ok:
        raise AppError(
            ErrorCode.COMANDA_DESATUALIZADA,
            "Comanda foi alterada por outro usuário, recarregue",
            http_status=409,
        )

    item_c_qtd = item_c.quantidade
    item_c_produto_id = item_c.produto_id
    comandas_repository.cancelar_item(db, item_comanda_id, data.motivo.value, data.estornado)
    _liberar_reserva_estoque(db, item_c_produto_id, item_c_qtd)
    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.ITEM_CANCELADO,
        {
            "item_comanda_id": item_comanda_id,
            "motivo": data.motivo.value,
            "estornado": data.estornado,
        },
    )
    db.commit()
    comanda = comandas_repository.get_by_id(db, comanda_id)
    logger.info(
        "comanda_item_cancelado",
        comanda_id=comanda_id,
        tenant_id=comanda.tenant_id if comanda else None,  # type: ignore[union-attr]
        item_comanda_id=item_comanda_id,
        motivo=data.motivo.value,
    )
    return _build_response(db, comanda)  # type: ignore[arg-type]


def get_top_itens(db: Session, dias: int, limit: int) -> list[ProdutoResponse]:
    return produtos_service.get_top_produtos(db, dias, limit)


def aplicar_desconto(db: Session, comanda_id: int, data: AplicarDescontoRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    ok = comandas_repository.increment_version(db, comanda_id, data.version, comanda.tenant_id)
    if not ok:
        raise AppError(ErrorCode.COMANDA_DESATUALIZADA, "Versão desatualizada", http_status=409)

    if data.desconto_valor is not None:
        itens = comandas_repository.get_itens_para_fechar(db, comanda_id)
        subtotal: Decimal = sum((ic.preco_unitario * ic.quantidade for ic in itens), Decimal("0"))
        if data.desconto_valor > subtotal:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                f"Desconto (R$ {data.desconto_valor}) não pode ser maior que o subtotal (R$ {subtotal})",
                http_status=400,
            )

    comandas_repository.atualizar_desconto(db, comanda_id, data.desconto_percentual, data.desconto_valor)
    comandas_repository.add_evento(
        db,
        comanda_id,
        TipoEvento.DESCONTO_APLICADO,
        {
            "desconto_percentual": str(data.desconto_percentual) if data.desconto_percentual is not None else None,
            "desconto_valor": str(data.desconto_valor) if data.desconto_valor is not None else None,
        },
    )
    db.commit()
    db.refresh(comanda)
    return _build_response(db, comanda)


def fechar_comanda(db: Session, comanda_id: int, data: FecharComandaRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    _lock_comanda(db, comanda_id, data.version, comanda.tenant_id)

    if data.modo_divisao == "por_pessoa":
        pessoas = _parse_pessoas(comanda.pessoas)
        if len(pessoas) < 2:
            raise AppError(
                ErrorCode.PESSOAS_INSUFICIENTES,
                "Divisão por pessoa exige ao menos 2 pessoas cadastradas na comanda",
                http_status=400,
            )

    itens = comandas_repository.get_itens_para_fechar(db, comanda_id)
    subtotal: Decimal = sum((ic.preco_unitario * ic.quantidade for ic in itens), Decimal("0"))

    total_pago: Decimal = sum((p.valor for p in data.pagamentos), Decimal("0"))
    pagamento_parcial = data.modo_divisao == "parcial"

    if comanda.desconto_percentual is not None:
        total_com_desconto: Decimal = subtotal * (Decimal("1") - comanda.desconto_percentual / Decimal("100"))
        comanda.desconto_valor = (subtotal - total_com_desconto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    elif comanda.desconto_valor is not None:
        total_com_desconto = subtotal - comanda.desconto_valor
    else:
        total_com_desconto = subtotal

    if pagamento_parcial:
        base_parcial: Decimal = comanda.saldo_pendente if comanda.saldo_pendente is not None else total_com_desconto
        if total_pago >= base_parcial:
            raise AppError(
                ErrorCode.PAGAMENTO_NAO_BATE,
                "Pagamento parcial deve ser menor que o total",
                http_status=400,
            )
    else:
        base_total: Decimal = comanda.saldo_pendente if comanda.saldo_pendente is not None else total_com_desconto
        esperado: Decimal = (
            (base_total * _TAXA_SERVICO_MULTIPLICADOR) if data.taxa_servico else base_total
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if abs(total_pago - esperado) > Decimal("0.01"):
            raise AppError(
                ErrorCode.PAGAMENTO_NAO_BATE,
                f"Soma dos pagamentos (R$ {total_pago}) nao confere com o total (R$ {base_total})",
                http_status=400,
            )

    for p in data.pagamentos:
        metodo = db.get(MetodoPagamento, p.metodo_id)
        if metodo is None:
            raise AppError(ErrorCode.NOT_FOUND, f"Metodo de pagamento {p.metodo_id} nao encontrado", http_status=404)
        valor_nota: Optional[Decimal] = None
        troco: Optional[Decimal] = None
        if metodo.tipo == "dinheiro" and p.valor_nota is not None:
            if p.valor_nota < p.valor:
                raise AppError(
                    ErrorCode.PAGAMENTO_NAO_BATE,
                    "Valor da nota é inferior ao valor do pagamento",
                    http_status=400,
                )
            valor_nota = p.valor_nota
            troco = (p.valor_nota - p.valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        pagamentos_repository.create_pagamento(db, comanda_id, p.metodo_id, p.valor, valor_nota, troco)

    itens_negativos: list[str] = []

    if pagamento_parcial:
        novo_saldo: Decimal = base_parcial - total_pago
        comandas_repository.atualizar_saldo_pendente(db, comanda_id, novo_saldo)
    else:
        for ic in itens:
            negativos = _dar_baixa_estoque(db, ic.produto_id, ic.quantidade)
            itens_negativos.extend(negativos)
            _liberar_reserva_estoque(db, ic.produto_id, ic.quantidade)
        comandas_repository.fechar_comanda_repo(db, comanda_id, esperado)

    if not pagamento_parcial and data.taxa_servico and comanda.garcom_id is not None:
        valor_comissao = (
            total_com_desconto * TAXA_SERVICO_PERCENTUAL / Decimal("100")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        comissao = ComissaoGarcom(
            garcom_id=comanda.garcom_id,
            comanda_id=comanda_id,
            valor=valor_comissao,
            percentual=TAXA_SERVICO_PERCENTUAL,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(comissao)

    db.commit()
    db.refresh(comanda)
    logger.info(
        "comanda_fechada",
        comanda_id=comanda_id,
        tenant_id=comanda.tenant_id,
        modo_divisao=data.modo_divisao,
        taxa_servico=bool(data.taxa_servico),
    )
    if itens_negativos:
        logger.warning(
            "comanda_fechada_com_estoque_negativo",
            comanda_id=comanda_id,
            tenant_id=comanda.tenant_id,
            insumos=itens_negativos,
        )
    response = _build_response(db, comanda)
    response.itens_negativos = itens_negativos
    return response


def _reservar_estoque(db: Session, produto_id: int, quantidade: Decimal) -> list[str]:
    def ajustar(insumo: Insumo, qty: Decimal) -> Optional[str]:
        insumo.estoque_reservado = insumo.estoque_reservado + qty
        disponivel = insumo.estoque_atual - insumo.estoque_reservado
        return insumo.nome if disponivel < 0 else None

    return estoque_repository.ajustar_estoque_ficha_tecnica(db, produto_id, quantidade, ajustar)


def _liberar_reserva_estoque(db: Session, produto_id: int, quantidade: Decimal) -> None:
    def ajustar(insumo: Insumo, qty: Decimal) -> None:
        novo = insumo.estoque_reservado - qty
        insumo.estoque_reservado = novo if novo > Decimal("0") else Decimal("0")
        return None

    estoque_repository.ajustar_estoque_ficha_tecnica(db, produto_id, quantidade, ajustar)


def cancelar_comanda(db: Session, comanda_id: int, data: CancelarComandaRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status not in _ABERTA_STATUSES:
        raise AppError(ErrorCode.COMANDA_FECHADA, "Comanda não está aberta", http_status=400)

    ok = comandas_repository.increment_version(db, comanda_id, data.version, comanda.tenant_id)
    if not ok:
        raise AppError(ErrorCode.COMANDA_DESATUALIZADA, "Versão desatualizada", http_status=409)

    itens = comandas_repository.get_itens_para_fechar(db, comanda_id)
    for ic in itens:
        _liberar_reserva_estoque(db, ic.produto_id, ic.quantidade)

    comandas_repository.cancelar_comanda_repo(db, comanda_id)
    comandas_repository.add_evento(db, comanda_id, TipoEvento.COMANDA_EDITADA, {"cancelada": True})
    db.commit()
    db.refresh(comanda)
    logger.info("comanda_cancelada", comanda_id=comanda_id, tenant_id=comanda.tenant_id)
    return _build_response(db, comanda)


def _dar_baixa_estoque(db: Session, produto_id: int, quantidade: Decimal) -> list[str]:
    def ajustar(insumo: Insumo, qty: Decimal) -> Optional[str]:
        negativos = _baixar_insumo(db, insumo, qty)
        return negativos[0] if negativos else None

    # flush_each=False: _baixar_insumo já dá flush internamente (via
    # estoque_repository.registrar_movimento), então não é preciso flush
    # duplicado aqui.
    return estoque_repository.ajustar_estoque_ficha_tecnica(
        db, produto_id, quantidade, ajustar, flush_each=False
    )


def _baixar_insumo(db: Session, insumo: Insumo, quantidade: Decimal) -> list[str]:
    novo_estoque = insumo.estoque_atual - quantidade
    insumo.estoque_atual = novo_estoque
    estoque_repository.registrar_movimento(
        db,
        insumo_id=insumo.id,
        tipo=TipoMovimento.SAIDA_VENDA,
        quantidade=quantidade,
        custo_unitario=insumo.custo_medio,
        saldo_apos=novo_estoque,
    )
    db.flush()
    return [insumo.nome] if novo_estoque < 0 else []


def reabrir_comanda(db: Session, comanda_id: int, data: ReabrirComandaRequest) -> ComandaResponse:
    comanda = comandas_repository.get_by_id(db, comanda_id)
    if comanda is None:
        raise AppError(ErrorCode.NOT_FOUND, "Comanda não encontrada", http_status=404)
    if comanda.status != StatusComanda.FECHADA.value:
        raise AppError(
            ErrorCode.COMANDA_NAO_FECHADA,
            "Apenas comandas fechadas podem ser reabertas",
            http_status=400,
        )

    _lock_comanda(db, comanda_id, data.version, comanda.tenant_id)

    itens = comandas_repository.get_itens_para_fechar(db, comanda_id)
    for ic in itens:
        _estornar_estoque(db, ic.produto_id, ic.quantidade)
        _reservar_estoque(db, ic.produto_id, ic.quantidade)

    db.query(Pagamento).filter(Pagamento.comanda_id == comanda_id).delete()
    db.query(ComissaoGarcom).filter(ComissaoGarcom.comanda_id == comanda_id).delete()

    comandas_repository.reabrir_comanda_repo(db, comanda_id)
    comandas_repository.add_evento(
        db, comanda_id, TipoEvento.COMANDA_REABERTA, {}, comanda.garcom_id
    )

    db.commit()
    db.refresh(comanda)
    return _build_response(db, comanda)


def _estornar_estoque(db: Session, produto_id: int, quantidade: Decimal) -> None:
    def ajustar(insumo: Insumo, qty: Decimal) -> None:
        _estornar_insumo(db, insumo, qty)
        return None

    # flush_each=False: _estornar_insumo já dá flush internamente (via
    # estoque_repository.registrar_movimento), então não é preciso flush
    # duplicado aqui.
    estoque_repository.ajustar_estoque_ficha_tecnica(
        db, produto_id, quantidade, ajustar, flush_each=False
    )


def _estornar_insumo(db: Session, insumo: Insumo, quantidade: Decimal) -> None:
    novo_estoque = insumo.estoque_atual + quantidade
    insumo.estoque_atual = novo_estoque
    estoque_repository.registrar_movimento(
        db,
        insumo_id=insumo.id,
        tipo=TipoMovimento.ENTRADA_ESTORNO,
        quantidade=quantidade,
        custo_unitario=insumo.custo_medio,
        saldo_apos=novo_estoque,
    )
    db.flush()

import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PagamentoResumo(BaseModel):
    metodo_id: int
    metodo_nome: str
    total: Decimal
    qtd: int


class ComandaRelatorioItem(BaseModel):
    id: int
    identificacao: str
    garcom_nome: str
    total: Decimal
    desconto_percentual: Optional[Decimal]
    desconto_valor: Optional[Decimal]
    cortesias: Decimal
    data_fechamento: datetime.datetime
    pagamentos: list[PagamentoResumo]


class VendasDoDiaResponse(BaseModel):
    data: datetime.date
    qtd_comandas: int
    faturamento_bruto: Decimal
    total_descontos: Decimal
    total_cortesias: Decimal
    total_comissoes: Decimal
    faturamento_liquido: Decimal
    por_metodo: list[PagamentoResumo]
    comandas: list[ComandaRelatorioItem]


class HistoricoResponse(BaseModel):
    total: int
    comandas: list[ComandaRelatorioItem]


class FechamentoCaixaResponse(BaseModel):
    data: datetime.date
    qtd_comandas: int
    faturamento_bruto: Decimal
    descontos: Decimal
    cortesias: Decimal
    total_comissoes: Decimal
    faturamento_liquido: Decimal
    por_metodo: list[PagamentoResumo]


class ItemSemCusto(BaseModel):
    item_id: int
    nome: str


class DREResponse(BaseModel):
    mes: str
    faturamento_bruto: Decimal
    descontos: Decimal
    cortesias_valor: Decimal
    faturamento_liquido: Decimal
    cmv: Decimal
    perdas: Decimal
    comissoes: Decimal
    total_custos: Decimal
    lucro_bruto: Decimal
    margem_percentual: Decimal
    produtos_sem_custo: list[ItemSemCusto]


class CMVProdutoItem(BaseModel):
    item_id: int
    nome: str
    preco_venda: Optional[Decimal]
    custo_medio: Optional[Decimal]
    margem_valor: Optional[Decimal]
    margem_percentual: Optional[Decimal]
    classificacao: str


class CMVPorProdutoResponse(BaseModel):
    itens: list[CMVProdutoItem]


class PerdasGrupo(BaseModel):
    motivo: str
    qtd_movimentos: int
    total_valor: Decimal


class PerdasCortesiasResponse(BaseModel):
    data_inicio: datetime.date
    data_fim: datetime.date
    total_geral: Decimal
    grupos: list[PerdasGrupo]


class VendasGarcomItem(BaseModel):
    garcom_id: int
    garcom_nome: str
    qtd_comandas: int
    faturamento: Decimal
    ticket_medio: Decimal
    comissao: Decimal


class VendasPorGarcomResponse(BaseModel):
    data_inicio: datetime.date
    data_fim: datetime.date
    garcons: list[VendasGarcomItem]


class ProdutoMaisVendidoItem(BaseModel):
    produto_id: int
    produto_nome: str
    categoria_nome: Optional[str]
    quantidade_total: Decimal
    receita_total: Decimal
    percentual_receita: Decimal


class ProdutosMaisVendidosResponse(BaseModel):
    data_inicio: datetime.date
    data_fim: datetime.date
    receita_total_periodo: Decimal
    itens: list[ProdutoMaisVendidoItem]


class HorarioPicoItem(BaseModel):
    hora: int
    total_comandas: int
    receita_total: Decimal


class PicoVendasHorarioResponse(BaseModel):
    data_inicio: datetime.date
    data_fim: datetime.date
    horarios: list[HorarioPicoItem]
    hora_pico: Optional[int]
    total_comandas_periodo: int
    receita_total_periodo: Decimal

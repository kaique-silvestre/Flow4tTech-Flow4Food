import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class NFeItemResponse(BaseModel):
    nome_xml: str
    ean_xml: Optional[str]
    quantidade: Decimal
    unidade_xml: str
    custo_unitario: Decimal
    custo_total: Decimal
    insumo_id: Optional[int]
    insumo_nome: Optional[str]


class NFeImportResponse(BaseModel):
    numero_nota: str
    data_compra: datetime.date
    cnpj_xml: str
    fornecedor_id: Optional[int]
    fornecedor_nome_xml: str
    itens: list[NFeItemResponse]

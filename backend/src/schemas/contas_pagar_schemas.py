import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContaPagarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    compra_id: Optional[int]
    fornecedor_id: Optional[int]
    fornecedor_nome: Optional[str] = None
    valor: Decimal
    data_vencimento: datetime.date
    data_pagamento: Optional[datetime.date]
    status: str
    metodo_pagamento_id: Optional[int]
    observacao: Optional[str]
    created_at: datetime.datetime


class ContasPagarPageResponse(BaseModel):
    itens: list[ContaPagarResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
    total_pendente: Decimal
    total_vencido: Decimal


class PagarContaRequest(BaseModel):
    metodo_pagamento_id: Optional[int] = None
    data_pagamento: datetime.date
    observacao: Optional[str] = None


class ContasPagarResumoResponse(BaseModel):
    pendente: int
    vencido: int
    total_vencido: Decimal


class NotificacaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: str
    referencia_id: Optional[int]
    mensagem: str
    lida: bool
    created_at: datetime.datetime

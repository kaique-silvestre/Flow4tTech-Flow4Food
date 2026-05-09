from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AplicarDescontoRequest(BaseModel):
    desconto_percentual: Optional[Decimal] = Field(None, ge=0, le=100)
    desconto_valor: Optional[Decimal] = Field(None, ge=0)

    @model_validator(mode="after")
    def validar_desconto(self) -> "AplicarDescontoRequest":
        tem_percentual = self.desconto_percentual is not None
        tem_valor = self.desconto_valor is not None
        if tem_percentual and tem_valor:
            raise ValueError("Informe apenas desconto_percentual ou desconto_valor, não ambos")
        return self


class PagamentoRequest(BaseModel):
    metodo_id: int
    valor: Decimal = Field(..., gt=0)


class FecharComandaRequest(BaseModel):
    pagamentos: list[PagamentoRequest] = Field(..., min_length=0)
    modo_divisao: Literal["sem_divisao", "igualmente", "por_pessoa", "parcial"]


class PagamentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metodo_id: int
    metodo_nome: str
    valor: Decimal

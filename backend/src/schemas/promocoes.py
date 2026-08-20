import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class PromoçaoCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None  # noqa: UP045
    tipo_desconto: str  # 'porcentagem' | 'valor_fixo'
    valor_desconto: Decimal = Field(gt=0)
    data_inicio: datetime.date
    data_fim: Optional[datetime.date] = None  # noqa: UP045
    hora_inicio: Optional[datetime.time] = datetime.time(0, 0, 0)  # noqa: UP045
    hora_fim: Optional[datetime.time] = datetime.time(23, 59, 59)  # noqa: UP045
    recorrencia: str = "nenhuma"  # 'nenhuma' | 'semanal' | 'mensal'
    dias_semana: Optional[list[int]] = None  # noqa: UP045
    dias_mes: Optional[list[int]] = None  # noqa: UP045
    produto_ids: list[int] = []
    ativo: bool = True

    @model_validator(mode="after")
    def validar_recorrencia(self) -> "PromoçaoCreate":
        if self.tipo_desconto not in ("porcentagem", "valor_fixo"):
            raise ValueError("tipo_desconto deve ser 'porcentagem' ou 'valor_fixo'")
        if self.tipo_desconto == "porcentagem" and self.valor_desconto > 100:
            raise ValueError("valor_desconto não pode exceder 100 quando tipo_desconto='porcentagem'")
        if self.data_fim is not None and self.data_fim < self.data_inicio:
            raise ValueError("data_fim deve ser >= data_inicio")
        if self.recorrencia == "nenhuma":
            if self.dias_semana:
                raise ValueError("dias_semana deve ser vazio quando recorrencia='nenhuma'")
            if self.dias_mes:
                raise ValueError("dias_mes deve ser vazio quando recorrencia='nenhuma'")
        elif self.recorrencia == "semanal":
            if not self.dias_semana:
                raise ValueError("dias_semana obrigatório quando recorrencia='semanal'")
            if any(d < 0 or d > 6 for d in self.dias_semana):
                raise ValueError("dias_semana: valores devem ser 0-6")
        elif self.recorrencia == "mensal":
            if not self.dias_mes:
                raise ValueError("dias_mes obrigatório quando recorrencia='mensal'")
            if any(d < 1 or d > 31 for d in self.dias_mes):
                raise ValueError("dias_mes: valores devem ser 1-31")
        else:
            raise ValueError("recorrencia deve ser 'nenhuma', 'semanal' ou 'mensal'")
        return self


class PromoçaoUpdate(BaseModel):
    nome: Optional[str] = None  # noqa: UP045
    descricao: Optional[str] = None  # noqa: UP045
    tipo_desconto: Optional[str] = None  # noqa: UP045
    valor_desconto: Optional[Decimal] = Field(default=None, gt=0)  # noqa: UP045
    data_inicio: Optional[datetime.date] = None  # noqa: UP045
    data_fim: Optional[datetime.date] = None  # noqa: UP045
    hora_inicio: Optional[datetime.time] = None  # noqa: UP045
    hora_fim: Optional[datetime.time] = None  # noqa: UP045
    recorrencia: Optional[str] = None  # noqa: UP045
    dias_semana: Optional[list[int]] = None  # noqa: UP045
    dias_mes: Optional[list[int]] = None  # noqa: UP045
    produto_ids: Optional[list[int]] = None  # noqa: UP045
    ativo: Optional[bool] = None  # noqa: UP045

    @model_validator(mode="after")
    def validar_campos(self) -> "PromoçaoUpdate":
        if self.tipo_desconto is not None and self.tipo_desconto not in ("porcentagem", "valor_fixo"):
            raise ValueError("tipo_desconto deve ser 'porcentagem' ou 'valor_fixo'")
        if (
            self.tipo_desconto == "porcentagem"
            and self.valor_desconto is not None
            and self.valor_desconto > 100
        ):
            raise ValueError("valor_desconto não pode exceder 100 quando tipo_desconto='porcentagem'")
        if self.data_inicio is not None and self.data_fim is not None and self.data_fim < self.data_inicio:
            raise ValueError("data_fim deve ser >= data_inicio")
        if self.recorrencia is not None:
            if self.recorrencia == "nenhuma":
                if self.dias_semana:
                    raise ValueError("dias_semana deve ser vazio quando recorrencia='nenhuma'")
                if self.dias_mes:
                    raise ValueError("dias_mes deve ser vazio quando recorrencia='nenhuma'")
            elif self.recorrencia == "semanal":
                if self.dias_semana is not None and not self.dias_semana:
                    raise ValueError("dias_semana obrigatório quando recorrencia='semanal'")
            elif self.recorrencia == "mensal":
                if self.dias_mes is not None and not self.dias_mes:
                    raise ValueError("dias_mes obrigatório quando recorrencia='mensal'")
            else:
                raise ValueError("recorrencia deve ser 'nenhuma', 'semanal' ou 'mensal'")
        return self


class PromoçaoResponse(BaseModel):
    id: int
    tenant_id: int
    nome: str
    descricao: Optional[str] = None  # noqa: UP045
    tipo_desconto: str
    valor_desconto: Decimal
    data_inicio: datetime.date
    data_fim: Optional[datetime.date] = None  # noqa: UP045
    hora_inicio: Optional[datetime.time] = None  # noqa: UP045
    hora_fim: Optional[datetime.time] = None  # noqa: UP045
    recorrencia: str
    dias_semana: Optional[list[int]] = None  # noqa: UP045
    dias_mes: Optional[list[int]] = None  # noqa: UP045
    produto_ids: list[int] = []
    criado_por: Optional[int] = None  # noqa: UP045
    created_at: Optional[datetime.datetime] = None  # noqa: UP045
    ativo: bool = True

    model_config = {"from_attributes": True}

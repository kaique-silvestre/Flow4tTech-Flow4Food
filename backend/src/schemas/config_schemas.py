from typing import Optional

from pydantic import BaseModel


class EstabelecimentoResponse(BaseModel):
    id: int
    nome: str
    cnpj: Optional[str]
    endereco: Optional[str]
    telefone: Optional[str]

    model_config = {"from_attributes": True}


class EstabelecimentoUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    endereco: Optional[str] = None
    telefone: Optional[str] = None


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str

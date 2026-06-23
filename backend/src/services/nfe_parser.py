"""Pure NF-e XML parser — zero DB access."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

from src.core.errors import AppError, ErrorCode

_NS = "http://www.portalfiscal.inf.br/nfe"
_TAG = f"{{{_NS}}}"

_UNIDADE_MAP: dict[str, str] = {
    "KG": "kg",
    "K": "kg",
    "GR": "g",
    "G": "g",
    "UN": "un",
    "UND": "un",
    "PC": "un",
    "PÇ": "un",
    "CX": "un",
    "LT": "un",
    "L": "un",
    "ML": "un",
    "MT": "un",
    "M": "un",
}


@dataclass
class NFeItem:
    nome: str
    ean: Optional[str]
    quantidade: Decimal
    unidade_xml: str
    custo_unitario: Decimal
    custo_total: Decimal


@dataclass
class NFeData:
    numero_nota: str
    data_emissao: date
    cnpj_emitente: str
    nome_emitente: str
    itens: list[NFeItem] = field(default_factory=list)


def _find(element: ET.Element, path: str) -> Optional[ET.Element]:
    return element.find(f"{_TAG}{path.replace('/', f'/{_TAG}')}")


def _text(element: ET.Element, path: str, default: str = "") -> str:
    el = _find(element, path)
    return (el.text or "").strip() if el is not None else default


def _decimal(value: str) -> Decimal:
    try:
        return Decimal(value.replace(",", "."))
    except InvalidOperation:
        return Decimal("0")


def _map_unidade(ucom: str) -> str:
    return _UNIDADE_MAP.get(ucom.upper().strip(), "un")


def _parse_date(raw: str) -> date:
    """Accept ISO datetime (2024-01-15T...) or plain date (2024-01-15)."""
    return date.fromisoformat(raw[:10])


def parse_nfe(xml_bytes: bytes) -> NFeData:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise AppError(ErrorCode.VALIDATION_ERROR, f"XML inválido: {exc}") from exc

    # Support both nfeProc (wrapper) and NFe (raw) as root
    tag = root.tag
    if tag == f"{_TAG}nfeProc":
        nfe_el = root.find(f"{_TAG}NFe")
    elif tag == f"{_TAG}NFe":
        nfe_el = root
    else:
        raise AppError(ErrorCode.VALIDATION_ERROR, "XML não é uma NF-e SEFAZ válida")

    if nfe_el is None:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Elemento NFe não encontrado no XML")

    inf = nfe_el.find(f"{_TAG}infNFe")
    if inf is None:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Elemento infNFe não encontrado")

    # Header
    ide = _find(inf, "ide")
    if ide is None:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Elemento ide não encontrado")

    numero_nota = _text(ide, "nNF")

    # Date: prefer dhEmi (datetime), fallback dEmi (date only)
    dh_emi = _text(ide, "dhEmi") or _text(ide, "dEmi")
    if not dh_emi:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Data de emissão não encontrada")
    try:
        data_emissao = _parse_date(dh_emi)
    except ValueError as exc:
        raise AppError(ErrorCode.VALIDATION_ERROR, f"Data inválida: {dh_emi}") from exc

    emit = _find(inf, "emit")
    if emit is None:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Elemento emit não encontrado")

    cnpj_emitente = _text(emit, "CNPJ")
    nome_emitente = _text(emit, "xFant") or _text(emit, "xNome")

    # Items
    itens: list[NFeItem] = []
    for det in inf.findall(f"{_TAG}det"):
        prod = det.find(f"{_TAG}prod")
        if prod is None:
            continue
        nome = _text(prod, "xProd")
        ean_raw = _text(prod, "cEAN")
        ean: Optional[str] = None if ean_raw.upper() in ("SEM GTIN", "", "0") else ean_raw
        quantidade = _decimal(_text(prod, "qCom", "0"))
        unidade_xml = _text(prod, "uCom", "UN")
        custo_unitario = _decimal(_text(prod, "vUnCom", "0"))
        custo_total = _decimal(_text(prod, "vProd", "0"))
        itens.append(NFeItem(
            nome=nome,
            ean=ean,
            quantidade=quantidade,
            unidade_xml=_map_unidade(unidade_xml),
            custo_unitario=custo_unitario,
            custo_total=custo_total,
        ))

    return NFeData(
        numero_nota=numero_nota,
        data_emissao=data_emissao,
        cnpj_emitente=cnpj_emitente,
        nome_emitente=nome_emitente,
        itens=itens,
    )

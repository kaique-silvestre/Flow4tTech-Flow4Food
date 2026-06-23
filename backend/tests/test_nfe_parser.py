import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

from decimal import Decimal

import pytest

from src.core.errors import AppError
from src.services.nfe_parser import parse_nfe

_NFE_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
  <NFe>
    <infNFe>
      <ide>
        <nNF>{nNF}</nNF>
        <dhEmi>{dhEmi}</dhEmi>
      </ide>
      <emit>
        <CNPJ>{cnpj}</CNPJ>
        <xNome>{xNome}</xNome>
      </emit>
      {dets}
    </infNFe>
  </NFe>
</nfeProc>
"""

_DET_TEMPLATE = """\
<det>
  <prod>
    <xProd>{xProd}</xProd>
    <cEAN>{cEAN}</cEAN>
    <qCom>{qCom}</qCom>
    <uCom>{uCom}</uCom>
    <vUnCom>{vUnCom}</vUnCom>
    <vProd>{vProd}</vProd>
  </prod>
</det>
"""


def _make_xml(
    nNF="42",
    dhEmi="2024-03-15T10:00:00-03:00",
    cnpj="12345678000195",
    xNome="Distribuidora Teste",
    dets=None,
) -> bytes:
    if dets is None:
        dets = _DET_TEMPLATE.format(
            xProd="Arroz 5kg", cEAN="7891234567890", qCom="10", uCom="UN", vUnCom="15.50", vProd="155.00"
        )
    xml = _NFE_TEMPLATE.format(nNF=nNF, dhEmi=dhEmi, cnpj=cnpj, xNome=xNome, dets=dets)
    return xml.encode("utf-8")


def test_parse_valid_single_item():
    result = parse_nfe(_make_xml())
    assert result.numero_nota == "42"
    assert str(result.data_emissao) == "2024-03-15"
    assert result.cnpj_emitente == "12345678000195"
    assert result.nome_emitente == "Distribuidora Teste"
    assert len(result.itens) == 1
    item = result.itens[0]
    assert item.nome == "Arroz 5kg"
    assert item.ean == "7891234567890"
    assert item.quantidade == Decimal("10")
    assert item.custo_unitario == Decimal("15.50")
    assert item.custo_total == Decimal("155.00")


def test_parse_multiple_items():
    dets = _DET_TEMPLATE.format(xProd="Feijão", cEAN="SEM GTIN", qCom="5", uCom="KG", vUnCom="8.00", vProd="40.00")
    dets += _DET_TEMPLATE.format(xProd="Sal", cEAN="0", qCom="2", uCom="UN", vUnCom="3.00", vProd="6.00")
    result = parse_nfe(_make_xml(dets=dets))
    assert len(result.itens) == 2


def test_ean_sem_gtin_becomes_none():
    det = _DET_TEMPLATE.format(xProd="Óleo", cEAN="SEM GTIN", qCom="1", uCom="LT", vUnCom="9.00", vProd="9.00")
    result = parse_nfe(_make_xml(dets=det))
    assert result.itens[0].ean is None


def test_ean_zero_becomes_none():
    det = _DET_TEMPLATE.format(xProd="Pimenta", cEAN="0", qCom="1", uCom="UN", vUnCom="2.00", vProd="2.00")
    result = parse_nfe(_make_xml(dets=det))
    assert result.itens[0].ean is None


def test_unit_mapping_kg():
    det = _DET_TEMPLATE.format(xProd="Açúcar", cEAN="111", qCom="10", uCom="KG", vUnCom="3.00", vProd="30.00")
    result = parse_nfe(_make_xml(dets=det))
    assert result.itens[0].unidade_xml == "kg"


def test_unit_mapping_gr():
    det = _DET_TEMPLATE.format(xProd="Sal fino", cEAN="222", qCom="500", uCom="GR", vUnCom="0.01", vProd="5.00")
    result = parse_nfe(_make_xml(dets=det))
    assert result.itens[0].unidade_xml == "g"


def test_unit_mapping_cx_becomes_un():
    det = _DET_TEMPLATE.format(xProd="Caixinha", cEAN="333", qCom="2", uCom="CX", vUnCom="10.00", vProd="20.00")
    result = parse_nfe(_make_xml(dets=det))
    assert result.itens[0].unidade_xml == "un"


def test_unit_unknown_defaults_to_un():
    det = _DET_TEMPLATE.format(xProd="Mistério", cEAN="444", qCom="1", uCom="XYZ", vUnCom="1.00", vProd="1.00")
    result = parse_nfe(_make_xml(dets=det))
    assert result.itens[0].unidade_xml == "un"


def test_invalid_xml_raises_app_error():
    with pytest.raises(AppError):
        parse_nfe(b"not xml at all")


def test_wrong_namespace_raises_app_error():
    xml = b"""<?xml version="1.0"?><root xmlns="http://other.namespace.com"><child/></root>"""
    with pytest.raises(AppError):
        parse_nfe(xml)


def test_nfe_raw_root_without_proc():
    """NFe root directly (no nfeProc wrapper)."""
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
  <infNFe>
    <ide><nNF>99</nNF><dhEmi>2024-06-01T08:00:00-03:00</dhEmi></ide>
    <emit><CNPJ>99999999000100</CNPJ><xNome>Fornecedor Raw</xNome></emit>
    <det>
      <prod>
        <xProd>Produto X</xProd><cEAN>SEM GTIN</cEAN>
        <qCom>3</qCom><uCom>UN</uCom><vUnCom>5.00</vUnCom><vProd>15.00</vProd>
      </prod>
    </det>
  </infNFe>
</NFe>
""".encode("utf-8")
    result = parse_nfe(xml)
    assert result.numero_nota == "99"
    assert len(result.itens) == 1

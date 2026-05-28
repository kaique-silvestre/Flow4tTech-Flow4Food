"""Seed de dados de teste — categorias, produtos, insumos, fornecedores."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from decimal import Decimal
from src.core.database import SessionLocal
from src.models.categorias import Categoria
from src.models.produtos import Produto
from src.models.insumos import Insumo, UnidadeBase
from src.models.fornecedores import Fornecedor

db = SessionLocal()

# ── Fornecedores ────────────────────────────────────────────────
fornecedores_data = [
    {"nome": "Ambev Distribuidora",         "telefone": "(11) 3000-1000", "email": "pedidos@ambev.com.br"},
    {"nome": "Casa das Bebidas",             "telefone": "(11) 9 9800-2200", "email": "contato@casadebebidas.com.br"},
    {"nome": "Distribuidora Silva & Filhos", "telefone": "(11) 9 9700-3300", "email": "silva@distribuidora.com.br"},
    {"nome": "Hortifruti Central",           "telefone": "(11) 9 9600-4400", "email": None},
    {"nome": "Frigorífico Bom Bife",         "telefone": "(11) 9 9500-5500", "email": "vendas@bombife.com.br"},
]
fornecedores = {}
for f in fornecedores_data:
    exists = db.query(Fornecedor).filter(Fornecedor.nome == f["nome"]).first()
    if not exists:
        obj = Fornecedor(**f)
        db.add(obj)
        db.flush()
        fornecedores[f["nome"]] = obj
    else:
        fornecedores[f["nome"]] = exists
db.commit()
print(f"Fornecedores: {db.query(Fornecedor).count()} total")

# ── Categorias ─────────────────────────────────────────────────
def get_or_create_cat(nome, parent_id=None):
    obj = db.query(Categoria).filter(Categoria.nome == nome).first()
    if not obj:
        obj = Categoria(nome=nome, parent_id=parent_id)
        db.add(obj)
        db.flush()
    return obj

bebidas   = get_or_create_cat("Bebidas")
cervejas  = get_or_create_cat("Cervejas",      bebidas.id)
drinks    = get_or_create_cat("Drinks",         bebidas.id)
refris    = get_or_create_cat("Refrigerantes",  bebidas.id)
agua_suco = get_or_create_cat("Água e Sucos",  bebidas.id)
comidas   = get_or_create_cat("Comidas")
porcoes   = get_or_create_cat("Porções",        comidas.id)
lanches   = get_or_create_cat("Lanches",        comidas.id)
sobrem    = get_or_create_cat("Sobremesas")
db.commit()
print(f"Categorias: {db.query(Categoria).count()} total")

# ── Produtos ───────────────────────────────────────────────────
produtos_data = [
    # Cervejas
    {"nome": "Heineken 600ml",       "categoria_id": cervejas.id,  "preco_venda": Decimal("16.00")},
    {"nome": "Brahma 600ml",         "categoria_id": cervejas.id,  "preco_venda": Decimal("12.00")},
    {"nome": "Corona Long Neck",     "categoria_id": cervejas.id,  "preco_venda": Decimal("14.00")},
    {"nome": "Skol 600ml",           "categoria_id": cervejas.id,  "preco_venda": Decimal("10.00")},
    {"nome": "Stella Artois 275ml",  "categoria_id": cervejas.id,  "preco_venda": Decimal("13.00")},
    # Drinks
    {"nome": "Caipirinha",           "categoria_id": drinks.id,    "preco_venda": Decimal("20.00")},
    {"nome": "Mojito",               "categoria_id": drinks.id,    "preco_venda": Decimal("25.00")},
    {"nome": "Gin Tônica",           "categoria_id": drinks.id,    "preco_venda": Decimal("28.00")},
    {"nome": "Drinque da Casa",      "categoria_id": drinks.id,    "preco_venda": Decimal("22.00")},
    {"nome": "Sex on the Beach",     "categoria_id": drinks.id,    "preco_venda": Decimal("24.00")},
    # Refrigerantes
    {"nome": "Coca-Cola Lata",       "categoria_id": refris.id,    "preco_venda": Decimal("7.00")},
    {"nome": "Guaraná Lata",         "categoria_id": refris.id,    "preco_venda": Decimal("6.00")},
    {"nome": "Soda Limonada",        "categoria_id": refris.id,    "preco_venda": Decimal("9.00")},
    {"nome": "Tônica",               "categoria_id": refris.id,    "preco_venda": Decimal("6.00")},
    # Água e Sucos
    {"nome": "Água Sem Gás 500ml",   "categoria_id": agua_suco.id, "preco_venda": Decimal("4.00")},
    {"nome": "Água Com Gás 500ml",   "categoria_id": agua_suco.id, "preco_venda": Decimal("5.00")},
    {"nome": "Suco de Laranja",      "categoria_id": agua_suco.id, "preco_venda": Decimal("12.00")},
    {"nome": "Suco de Maracujá",     "categoria_id": agua_suco.id, "preco_venda": Decimal("12.00")},
    # Porções
    {"nome": "Batata Frita",         "categoria_id": porcoes.id,   "preco_venda": Decimal("28.00")},
    {"nome": "Frango na Chapa",      "categoria_id": porcoes.id,   "preco_venda": Decimal("42.00")},
    {"nome": "Calabresa Acebolada",  "categoria_id": porcoes.id,   "preco_venda": Decimal("38.00")},
    {"nome": "Bolinho de Bacalhau",  "categoria_id": porcoes.id,   "preco_venda": Decimal("35.00")},
    {"nome": "Isca de Frango",       "categoria_id": porcoes.id,   "preco_venda": Decimal("40.00")},
    {"nome": "Carne Seca c/ Mandioca","categoria_id": porcoes.id,  "preco_venda": Decimal("55.00")},
    # Lanches
    {"nome": "X-Burguer",            "categoria_id": lanches.id,   "preco_venda": Decimal("30.00")},
    {"nome": "X-Bacon",              "categoria_id": lanches.id,   "preco_venda": Decimal("36.00")},
    {"nome": "Misto Quente",         "categoria_id": lanches.id,   "preco_venda": Decimal("16.00")},
    # Sobremesas
    {"nome": "Pudim",                "categoria_id": sobrem.id,    "preco_venda": Decimal("14.00")},
    {"nome": "Brownie com Sorvete",  "categoria_id": sobrem.id,    "preco_venda": Decimal("18.00")},
    {"nome": "Petit Gâteau",         "categoria_id": sobrem.id,    "preco_venda": Decimal("22.00")},
]
created = 0
for p in produtos_data:
    exists = db.query(Produto).filter(Produto.nome == p["nome"]).first()
    if not exists:
        db.add(Produto(**p))
        created += 1
db.commit()
print(f"Produtos: {db.query(Produto).count()} total ({created} criados)")

# ── Insumos ────────────────────────────────────────────────────
insumos_data = [
    {"nome": "Cerveja Heineken 600ml",  "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("48"), "nivel_critico": Decimal("12"), "custo_medio": Decimal("7.50")},
    {"nome": "Cerveja Brahma 600ml",    "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("72"), "nivel_critico": Decimal("24"), "custo_medio": Decimal("5.00")},
    {"nome": "Cerveja Corona LN",       "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("36"), "nivel_critico": Decimal("12"), "custo_medio": Decimal("6.50")},
    {"nome": "Cachaça 51",              "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("6"),  "nivel_critico": Decimal("2"),  "custo_medio": Decimal("28.00")},
    {"nome": "Rum Branco",              "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("4"),  "nivel_critico": Decimal("1"),  "custo_medio": Decimal("45.00")},
    {"nome": "Gin London Dry",          "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("3"),  "nivel_critico": Decimal("1"),  "custo_medio": Decimal("65.00")},
    {"nome": "Coca-Cola 2L",            "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("24"), "nivel_critico": Decimal("6"),  "custo_medio": Decimal("9.00")},
    {"nome": "Água Tônica Lata",        "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("48"), "nivel_critico": Decimal("12"), "custo_medio": Decimal("3.50")},
    {"nome": "Água Mineral 500ml",      "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("60"), "nivel_critico": Decimal("12"), "custo_medio": Decimal("1.80")},
    {"nome": "Limão",                   "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("5"),  "nivel_critico": Decimal("1"),  "custo_medio": Decimal("6.00")},
    {"nome": "Açúcar",                  "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("10"), "nivel_critico": Decimal("2"),  "custo_medio": Decimal("4.50")},
    {"nome": "Gelo",                    "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("20"), "nivel_critico": Decimal("5"),  "custo_medio": Decimal("1.50")},
    {"nome": "Batata Congelada",        "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("15"), "nivel_critico": Decimal("3"),  "custo_medio": Decimal("12.00")},
    {"nome": "Frango (peito)",          "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("8"),  "nivel_critico": Decimal("2"),  "custo_medio": Decimal("18.00")},
    {"nome": "Calabresa",               "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("5"),  "nivel_critico": Decimal("1"),  "custo_medio": Decimal("22.00")},
    {"nome": "Carne Moída",             "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("6"),  "nivel_critico": Decimal("2"),  "custo_medio": Decimal("32.00")},
    {"nome": "Carne Seca",              "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("4"),  "nivel_critico": Decimal("1"),  "custo_medio": Decimal("55.00")},
    {"nome": "Pão de Hambúrguer",       "unidade_base": UnidadeBase.UNIDADE,     "estoque_atual": Decimal("30"), "nivel_critico": Decimal("10"), "custo_medio": Decimal("1.50")},
    {"nome": "Queijo Fatiado",          "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("2"),  "nivel_critico": Decimal("0.5"),"custo_medio": Decimal("40.00")},
    {"nome": "Bacon",                   "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("2"),  "nivel_critico": Decimal("0.5"),"custo_medio": Decimal("35.00")},
    {"nome": "Laranja",                 "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("10"), "nivel_critico": Decimal("2"),  "custo_medio": Decimal("5.00")},
    {"nome": "Maracujá",                "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("4"),  "nivel_critico": Decimal("1"),  "custo_medio": Decimal("8.00")},
    {"nome": "Mandioca Congelada",      "unidade_base": UnidadeBase.QUILOGRAMA,  "estoque_atual": Decimal("6"),  "nivel_critico": Decimal("2"),  "custo_medio": Decimal("10.00")},
]
created = 0
for ins in insumos_data:
    exists = db.query(Insumo).filter(Insumo.nome == ins["nome"]).first()
    if not exists:
        db.add(Insumo(**ins))
        created += 1
db.commit()
print(f"Insumos: {db.query(Insumo).count()} total ({created} criados)")

db.close()
print("\nSeed concluído.")

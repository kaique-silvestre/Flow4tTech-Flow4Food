# PRD — Importação Automática de NF-e XML para Compras

## Problem Statement

Ao receber mercadorias de fornecedores, o operador precisa registrar a compra no sistema item por item: seleciona o insumo, digita a quantidade, digita o custo. Para pedidos com 10, 20, 30 itens isso leva muitos minutos e é propenso a erros de digitação.

Fornecedores brasileiros emitem Nota Fiscal Eletrônica (NF-e) no padrão SEFAZ, que inclui um arquivo XML estruturado com todos os itens, quantidades, valores e CNPJ do emitente. Esse dado já existe — só precisa ser lido.

## Solution

Adicionar um botão **"Importar NF-e"** na listagem de compras. O operador faz upload do XML da NF-e, o sistema parseia o arquivo, tenta associar cada item a um insumo já cadastrado (por EAN ou nome fuzzy) e exibe uma **tela de revisão**. Itens não encontrados aparecem destacados com opção de criar o insumo inline (via modal já existente). Depois de revisar e confirmar, o sistema cria a compra e atualiza o estoque exatamente como faria pelo formulário manual.

## User Stories

1. Como operador de compras, quero fazer upload de um XML de NF-e, para não precisar digitar cada item manualmente.
2. Como operador de compras, quero que o fornecedor seja selecionado automaticamente quando o CNPJ do XML bater com um cadastrado, para economizar uma etapa.
3. Como operador de compras, quero ver os dados da nota (número, data, fornecedor) já preenchidos na tela de revisão, para verificar rapidamente se o XML é o correto.
4. Como operador de compras, quero ver cada item do XML com sua quantidade e valor, para conferir antes de confirmar.
5. Como operador de compras, quero que itens já cadastrados sejam associados automaticamente (por EAN ou nome), para não precisar vincular manualmente os que já existem.
6. Como operador de compras, quero ver itens sem match destacados em amarelo com label "Novo", para saber exatamente o que precisa de atenção.
7. Como operador de compras, quero clicar em "Criar insumo" em um item sem match e ter o modal de criação pré-preenchido com nome e unidade do XML, para criar o insumo sem redigitar os dados.
8. Como operador de compras, quero poder ignorar um item do XML (removê-lo da revisão), para não importar itens que não pertencem ao estoque do restaurante (ex: descarte, serviços).
9. Como operador de compras, quero poder corrigir a associação de um item (trocar o insumo sugerido por outro), para casos em que o nome do XML não bate exatamente com o cadastro.
10. Como operador de compras, quero poder ajustar a quantidade e o custo de um item antes de confirmar, para corrigir divergências entre nota e recebimento físico.
11. Como operador de compras, quero que o botão de confirmação fique bloqueado enquanto houver itens sem insumo associado, para não criar uma compra com itens inválidos.
12. Como operador de compras, quero que ao confirmar a compra seja criada com status "recebido" e o estoque seja atualizado imediatamente, para o fluxo ser igual ao formulário manual.
13. Como operador de compras, quero que o número da nota seja preenchido automaticamente do XML, para não precisar digitar o campo `numero_nota`.
14. Como operador de compras, quero receber um aviso se o número da nota já existir no sistema, para detectar duplicatas antes de confirmar.
15. Como gerente, quero que o campo CNPJ seja armazenado por fornecedor, para o match automático funcionar mesmo que o nome do fornecedor no XML seja diferente do cadastro.
16. Como gerente, quero que o código EAN seja armazenado por insumo, para o match por código seja possível em notas futuras do mesmo fornecedor.
17. Como desenvolvedor, quero que o parser NF-e seja uma função pura isolada, para poder testar sem banco de dados.

## Implementation Decisions

### Schema Changes

- **Fornecedor**: adicionar coluna `cnpj VARCHAR(14) NULL` — usado para auto-match quando CNPJ do XML bater.
- **Insumo**: adicionar coluna `ean VARCHAR(14) NULL` — código EAN/GTIN extraído do XML para match prioritário em futuras importações.
- Ambas as colunas são opcionais (NULL) e sem constraint de unicidade por ora.
- Duas migrations Alembic, uma por tabela (padrão `00{N}_{descricao}.py`).

### Backend Modules

**1. NF-e XML Parser** (`services/nfe_parser.py`)
- Função pura: recebe `bytes` de XML, retorna dataclass com:
  - `numero_nota`, `data_emissao: date`, `cnpj_emitente`, `nome_emitente`
  - `itens: list[NFeItem]` onde cada `NFeItem` tem: `nome`, `ean`, `quantidade: Decimal`, `unidade_xml`, `custo_unitario: Decimal`, `custo_total: Decimal`
- Zero acesso ao banco. Lança `AppError(VALIDATION_ERROR)` se XML inválido ou não for NF-e.
- Suporta namespace padrão SEFAZ `http://www.portalfiscal.inf.br/nfe`.

**2. NF-e Match Service** (`services/nfe_match_service.py`)
- Recebe dados parseados + `Session` do banco.
- Resolve fornecedor: busca `Fornecedor` por CNPJ → retorna `fornecedor_id` ou `None`.
- Para cada item: tenta match por EAN (exato), depois por nome (comparação case-insensitive, sem acentos). Retorna `insumo_id` e `insumo_nome` se encontrado, `None` se não.
- Não modifica banco — só lê.

**3. Endpoint** `POST /compras/importar-nfe`
- Aceita `multipart/form-data` com campo `file` (XML bytes).
- Chama parser → chama match service → retorna `NFeImportResponse`:
  ```
  {
    numero_nota, data_compra, fornecedor_id, fornecedor_nome_xml, cnpj_xml,
    itens: [{
      nome_xml, ean_xml, quantidade, unidade_xml,
      custo_unitario, custo_total,
      insumo_id, insumo_nome,   // null = sem match
    }]
  }
  ```
- Não persiste nada. Só parseia e resolve.
- Protegido pela permission `"compras"` (igual aos outros endpoints de compras).

**4. Frontend — `ImportarNFeModal`**
- Modal de upload disparado pelo botão "Importar NF-e" na `ComprasPage`.
- Estado 1 (upload): drag-and-drop ou file picker de `.xml`.
- Estado 2 (revisão): exibe todos os campos e a lista de itens.
  - Itens com `insumo_id` → linha normal com select pré-selecionado.
  - Itens com `insumo_id = null` → linha amarela com label "Novo" + botão "Criar insumo" que abre `InsumoModal` pré-preenchido (nome + unidade).
  - Cada linha editável: select de insumo, quantidade, custo total.
  - Botão "×" remove o item da lista.
- Botão "Confirmar compra" só habilitado quando todos os itens têm `insumo_id`.
- Ao confirmar, chama `POST /compras` (`criar_compra`) com `tipo_compra: "imediata"` e todos os itens resolvidos, depois invalida query e fecha modal.

**5. Schema Pydantic**
- `NFeImportResponse` (response do endpoint de parse)
- Sem novo schema de criação — reutiliza `CompraCreateRequest` existente na confirmação.

### Unidade XML → `unidade_base`

O XML usa strings livres (`UN`, `KG`, `GR`, `CX`, etc.). O parser faz mapeamento best-effort para `UnidadeBase` (`un`, `kg`, `g`). Strings não reconhecidas padrão para `un`. O usuário pode corrigir no `InsumoModal` antes de criar.

### Tipo de Compra

Importação via NF-e sempre cria como `tipo_compra = "imediata"` (recebe agora, paga na hora). Tipos agendados/a prazo ficam fora do escopo desta funcionalidade.

## Testing Decisions

**O que testar:** comportamento externo das funções puras, não detalhes de implementação.

**Módulo a testar: `nfe_parser.py`**
- Boa referência de estilo: `compraCalculations.test.ts` no frontend (testa função pura com inputs/outputs).
- Testes unitários em Python (`pytest`), sem banco de dados.
- Fixtures: XMLs de NF-e reais (anonimizados) ou sintéticos cobrindo:
  - NF-e válida com múltiplos itens → verifica count, valores, EANs
  - Item com EAN vazio (`cEAN = "SEM GTIN"`) → `ean = None`
  - Unidades diversas (`KG`, `GR`, `UN`, `CX`) → mapeamento correto
  - XML inválido (HTML, JSON, NF-e malformada) → levanta `AppError`
  - NF-e sem namespace esperado → levanta `AppError`

**Módulo a testar: `nfe_match_service.py`**
- Testa com banco SQLite in-memory (padrão do projeto).
- Casos: CNPJ bate com fornecedor → retorna id correto; CNPJ não bate → `None`; EAN bate com insumo → match; nome case-insensitive sem acento bate → match; sem match → `None`.

## Out of Scope

- Importação por foto/imagem (OCR + Vision AI)
- NF-e de serviço (modelo 55 com serviços, não mercadoria)
- Import em lote de múltiplos XMLs ao mesmo tempo
- Consulta de NF-e diretamente na SEFAZ (Webservice ou QR Code)
- Lookup de EAN em base pública (Open Food Facts, etc.)
- Validação de assinatura digital do XML
- Criação automática de fornecedor novo (apenas seleciona existente ou deixa em branco)
- Tipos de compra agendada ou a prazo via importação

## Further Notes

- O campo `numero_nota` já tem deduplicação de aviso no `compras_service.criar_compra()` — o aviso vai aparecer normalmente se a nota for importada duas vezes.
- Nenhum endpoint novo de criação — a confirmação chama o `POST /compras` existente, garantindo que toda a lógica de estoque (custo médio, movimentos, contas a pagar) fique centralizada no `criar_compra()`.
- `lxml` ou `xml.etree.ElementTree` (stdlib) são suficientes para o parser — sem dependência nova necessária.

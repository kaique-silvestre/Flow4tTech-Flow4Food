# Documentação Completa — Sistema Matchpoint

> **Sistema de gestão para bar/restaurante (comandas, estoque, CMV e fechamento)**
>
> **Cliente:** Estação Matchpoint
> **Data da reunião inicial:** 05/05/2026
> **Próxima reunião (entrega do MVP):** **12/05/2026 — 16h00**
> **Versão:** 2.0 — Documento unificado (fluxo + arquitetura)

---

## Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Contexto Operacional](#2-contexto-operacional)
3. [Modelo Comercial](#3-modelo-comercial)
4. [Tags e Convenções](#4-tags-e-convenções)
5. [Padrões Globais do Sistema](#5-padrões-globais-do-sistema)
6. [Modelo de Dados (Entidades)](#6-modelo-de-dados-entidades)
7. [Mapa de Telas](#7-mapa-de-telas)
8. [Fluxos Detalhados por Módulo](#8-fluxos-detalhados-por-módulo)
9. [Casos de Borda e Validações](#9-casos-de-borda-e-validações)
10. [Arquitetura Técnica (Deep Models)](#10-arquitetura-técnica-deep-models)
11. [Infraestrutura e Hospedagem](#11-infraestrutura-e-hospedagem)
12. [Cronograma de Desenvolvimento](#12-cronograma-de-desenvolvimento)
13. [Riscos e Mitigações](#13-riscos-e-mitigações)
14. [Critérios de Aceite do MVP](#14-critérios-de-aceite-do-mvp)
15. [Roadmap Pós-MVP](#15-roadmap-pós-mvp)
16. [Contatos e Próximos Passos](#16-contatos-e-próximos-passos)
17. [Anexos](#17-anexos)

---

## 1. Visão Geral do Projeto

A **Estação Matchpoint** é um bar localizado próximo a um campo de futebol, com forte movimento em dias de jogo e finais de semana. Hoje, **toda a operação é manual**: comandas em papel, sem controle de estoque digital, sem visão de CMV. Isso já gerou prejuízos concretos (ex: festa em que venderam ~10 vinhos e só 2 estavam marcados nas comandas).

O cliente avaliou um concorrente (sistema pronto, R$300 implantação + R$150/mês), mas optou por uma solução **personalizada, simples e mais barata** com a nossa equipe.

### 1.1 Princípio Norteador

> **"Simples, didático e funcional."**
>
> O cliente foi explícito: "não precisa limitar muito" e "vai ter gente mais velha mexendo". O sistema precisa ser óbvio para qualquer pessoa do caixa operar sem treinamento longo. Telas grandes, ações claras, mínimo de decisões por etapa.

---

## 2. Contexto Operacional

| Item | Situação Atual |
|------|----------------|
| Equipe fixa | 2 sócios + 1 senhora |
| Equipe pico (fim de semana / jogo) | Até 10 garçons freelancers |
| Maquininha | PagBank (sem integração) |
| Hardware disponível | 1 computador Dell novo (ainda sem uso) |
| Impressora | Obitech WD-80R7 (térmica) |
| Comanda atual | Papel físico, só para marcação e cobrança |
| Gestão financeira atual | Apenas planilha de custos |
| Tempo de operação do bar | 7 meses |

### 2.1 Principais Dores

1. **Garçons não marcam tudo** — esquecem ou fraudam ("ajudou 50, dá 100 cervejas")
2. **Sem visibilidade real de lucro** — só sabem o custo, não o ganho líquido
3. **Sem CMV** — não sabem a margem por produto
4. **Saídas sem venda não rastreadas** — consumo interno e perdas viram prejuízo invisível

---

## 3. Modelo Comercial

### 3.1 Etapas da Parceria

```
[Hoje - 05/05]      →      [12/05]      →      [12/05 → 12/06]      →      [Após 12/06]
     │                         │                      │                          │
     ▼                         ▼                      ▼                          ▼
Reunião de              Entrega do          1 mês de teste GRÁTIS         Contrato formal
levantamento             MVP cortesia       (ajustes semanais às         (implantação + mensalidade)
                                            terças, 16h)
```

### 3.2 MVP Cortesia

O MVP será entregue **gratuitamente**, como cortesia por serem um dos nossos primeiros clientes. Importante deixar claro em conversa e contrato:

> **O MVP é cortesia. Os valores de implantação e mensalidade futuros não incluem o desenvolvimento do MVP — eles cobrem a operação, manutenção e evolução contínua do sistema.**

### 3.3 Período de Teste (1 mês gratuito)

- **Início:** 12/05/2026 (entrega do MVP)
- **Término:** 12/06/2026
- **Rodadas de ajuste semanais:** toda **terça-feira às 16h00**, presencialmente no bar
- Durante esse período: ajustes ilimitados de bugs e refinamento de funcionalidades já entregues no MVP
- Novas funcionalidades fora do escopo do MVP podem ser discutidas e entrarão no roadmap pós-contrato

### 3.4 Contrato Pós-Teste

Após o mês de teste, os sócios escolhem um dos planos de parceria:

| Plano | Duração | Observação |
|-------|---------|------------|
| Trimestral | 3 meses | Compromisso curto |
| Semestral | 6 meses | — |
| Anual | 12 meses | Recomendado |
| Estendido | 18 meses | Maior desconto |

> **Valores de implantação e mensalidade:** A definir antes da assinatura.
> **Posicionamento:** Mais barato e mais personalizado que o concorrente (referência: R$300 + R$150/mês).
> **Orçamento estimado:** Implantação R$150-200 | Mensalidade R$100

---

## 4. Tags e Convenções

Cada funcionalidade descrita é marcada com uma tag indicando seu status:

| Tag | Significado |
|-----|-------------|
| `[MVP]` | Entrega em 12/05/2026 |
| `[Pós-MVP]` | Entra em alguma das rodadas semanais (mês de teste) |
| `[Roadmap]` | Pós-contrato, evolução de longo prazo |
| `[Confirmar]` | Depende de validação com o cliente |

---

## 5. Padrões Globais do Sistema

### 5.1 Layout Base

Todas as telas internas seguem o mesmo esqueleto:

```
┌────────────────────────────────────────────────────────────────────┐
│  [☰]  ESTAÇÃO MATCHPOINT                              [⚙]  [🚪]    │  ← Topbar fixa
├──────┬─────────────────────────────────────────────────────────────┤
│      │                                                             │
│  📊  │                                                             │
│  🍺  │                                                             │
│  🛒  │              ÁREA DE CONTEÚDO                                │
│  📦  │              (cada tela renderiza aqui)                      │
│  📋  │                                                             │
│  📈  │                                                             │
│  ⚙️  │                                                             │
│      │                                                             │
└──────┴─────────────────────────────────────────────────────────────┘
```

- **Topbar fixa**: nome do estabelecimento, botão de configurações rápidas, botão de sair.
- **Menu lateral expansível**: por padrão mostra só ícones; ao clicar no `☰`, expande mostrando ícone + texto.
- **Área de conteúdo**: renderiza a tela atual.

### 5.2 Menu Lateral

| Ícone | Item | Descrição |
|-------|------|-----------|
| 📊 | Dashboard | Home com indicadores e alertas |
| 🍺 | Comandas | Operação: abrir, lançar, fechar |
| 🛒 | Compras | Notas fiscais e entradas manuais |
| 📦 | Estoque | Saldo, baixa sem venda, histórico |
| 📋 | Cadastros | Itens, categorias, fornecedores, garçons, métodos de pagamento |
| 📈 | Relatórios | Vendas, DRE, fechamento de caixa, histórico |
| ⚙️ | Configurações | Dados do bar, senha, impressora |

### 5.3 Comportamentos Padrão

#### 5.3.1 Confirmação de Ações Destrutivas

**Toda ação destrutiva exige confirmação em modal**, com:
- Título claro ("Cancelar item?", "Reabrir comanda?", "Excluir produto?")
- Descrição do impacto (ex: "Esta ação irá reverter o item do estoque.")
- Dois botões: `[Cancelar]` (secundário) e `[Confirmar]` (vermelho/destrutivo)

Ações que exigem confirmação:
- Cancelar item lançado em comanda
- Aplicar baixa sem venda
- Reabrir comanda fechada
- Excluir qualquer cadastro (item, fornecedor, garçom, categoria)
- Aplicar cortesia (item com preço zero)
- Aplicar desconto

#### 5.3.2 Feedback de Sucesso (Toast)

Pop-up no **canto superior direito**, surge e desaparece sozinho:

| Tipo | Cor | Duração | Quando |
|------|-----|---------|--------|
| Sucesso | Verde | 2-3 segundos | Ação concluída (salvar, fechar comanda, etc.) |
| Erro | Vermelho | Permanente até fechar | Falha (não consegue salvar, validação) |
| Aviso | Amarelo | 4-5 segundos | Atenção (estoque baixo, comanda antiga) |

#### 5.3.3 Atalhos de Teclado

`[Pós-MVP]` — Não entram no MVP. Avaliar pós-contrato pra otimizar caixa em dia de jogo.

---

## 6. Modelo de Dados (Entidades)

### 6.1 Hierarquia Geral

```
FORNECEDOR ──┐
             ├──► COMPRA (manual no MVP, XML futuro)
             │       │
             │       ▼
             │     ITEM (insumo ou produto vendável)
             │       │
             │       ├──► FICHA TÉCNICA (se composto)
             │       │       └──► insumos vinculados com quantidades
             │       │
             │       ▼
             │     ESTOQUE (saldo atual)
             │       │
             │       ▼
             └──► COMANDA ──► VENDA ──► COMPROVANTE
                     │
                     └──► GARÇOM (responsável)
```

### 6.2 Entidades

#### Item (núcleo do sistema)

Modelagem unificada — substitui a separação rígida "insumo vs produto":

| Campo | Descrição |
|-------|-----------|
| `nome` | Ex: "Coca Lata 350ml", "Carne Moída", "X-Burguer" |
| `categoria` | Ex: Refrigerantes, Carnes, Lanches |
| `tipo` | `simples` ou `composto` |
| `vendavel` | `true` ou `false` (se aparece como opção em comanda) |
| `unidade_base` | `un` ou `g` (volume fica fora do MVP) |
| `quantidade_caixa` | Para itens em caixa (ex: 1 caixa de cerveja = 24 un) |
| `custo_medio` | Calculado por média ponderada nas compras |
| `preco_venda` | Definido pelo sócio |
| `cmv_percentual` | Calculado: (custo / preço) × 100 |
| `estoque_atual` | Saldo atualizado pelas movimentações |

**Casos cobertos pela modelagem:**

| Item | tipo | vendável | ficha técnica |
|------|------|----------|---------------|
| Coca Lata | simples | sim | não |
| Carne moída | simples | não | não |
| Queijo | simples | não | não |
| X-Burguer | composto | sim | sim (1 pão + 200g carne + 50g queijo) |
| Balde de 6 long necks | composto | sim | sim (6 long necks) |

#### Comanda

| Campo | Descrição |
|-------|-----------|
| `identificacao` | Nome do responsável OU número de mesa |
| `numero_sequencial` | Auto-gerado (#001, #002...) `[Pós-MVP]` |
| `garcom` | Vinculado no momento da abertura |
| `pessoas` | Lista de nomes (cliente João, cliente Maria...) |
| `itens` | Lista de itens lançados, cada um vinculado a uma pessoa |
| `status` | `aberta`, `fechada`, `reaberta` |
| `data_abertura` | Timestamp |
| `data_fechamento` | Timestamp |

#### Item da Comanda

| Campo | Descrição |
|-------|-----------|
| `item_id` | Referência ao Item |
| `quantidade` | Quantos foram pedidos |
| `preco_unitario` | Snapshot do preço no momento do lançamento |
| `pessoa_associada` | "João" / "Maria" / null |
| `observacao` | Texto livre ("sem cebola", "bem passado") |
| `cortesia` | Boolean (se sim, preço efetivo = 0) |
| `cancelado` | Boolean |
| `motivo_cancelamento` | Texto (quando cancelado) |
| `estornar_estoque` | Boolean (se cancelado, decide se volta ao estoque) |

#### Compra

| Campo | Descrição |
|-------|-----------|
| `fornecedor_id` | Referência ao Fornecedor |
| `data_compra` | Data informada |
| `numero_nota` | Opcional no MVP |
| `itens` | Lista de itens comprados, cada um com quantidade e custo |
| `valor_total` | Soma dos itens |
| `origem` | `manual` (MVP) / `xml` (Pós-MVP) |

#### Fornecedor

| Campo | Descrição |
|-------|-----------|
| `nome` | Razão social ou nome fantasia |
| `cnpj` | Opcional no MVP |
| `contato` | Telefone/email opcional |

#### Garçom

| Campo | Descrição |
|-------|-----------|
| `nome` | Nome do garçom |
| `ativo` | Boolean (se aparece nas opções de comanda) |

---

## 7. Mapa de Telas

### 7.1 Visão Hierárquica

```
🔐 Login

📊 Dashboard (home pós-login)
   ├── Cards de indicadores (faturamento, ticket médio, comandas, lucro)
   ├── Gráficos (hoje, 30 dias, calendário do mês)
   └── Lista rápida de comandas abertas

🍺 Comandas
   ├── Lista de comandas abertas
   ├── Nova comanda
   ├── Comanda aberta (lançamento de itens)
   ├── Fechamento de comanda (divisão + pagamento)
   └── Comprovante (impressão)

🛒 Compras
   ├── Lista de compras (histórico)
   └── Nova compra manual
   └── [Pós-MVP] Importar XML

📦 Estoque
   ├── Saldo atual
   ├── Baixa sem venda
   └── Histórico de movimentações

📋 Cadastros
   ├── Itens (com filtro: simples / composto / vendável)
   │   └── Cadastro/edição (com ficha técnica se composto)
   ├── Categorias
   ├── Fornecedores
   ├── Garçons
   └── Métodos de pagamento

📈 Relatórios
   ├── Vendas do dia
   ├── Histórico de comandas (com filtro)
   ├── Fechamento de caixa
   ├── DRE simplificado
   ├── CMV por produto
   ├── Perdas e cortesias
   └── Vendas por garçom

⚙️ Configurações
   ├── Dados do estabelecimento
   ├── Senha
   ├── Impressora
   └── Backup/exportação
```

---

## 8. Fluxos Detalhados por Módulo

### 8.1 Login e Acesso

#### Tela: Login `[MVP]`

Tela única de entrada. **Sem seleção de operador** — login único do estabelecimento.

```
┌────────────────────────────────────────┐
│                                        │
│         ESTAÇÃO MATCHPOINT             │
│                                        │
│         ┌────────────────────┐         │
│         │  Senha             │         │
│         └────────────────────┘         │
│                                        │
│         ┌────────────────────┐         │
│         │      ENTRAR        │         │
│         └────────────────────┘         │
│                                        │
└────────────────────────────────────────┘
```

**Fluxo:**
1. Usuário insere a senha única.
2. Se correta → vai para Dashboard.
3. Se incorreta → toast vermelho "Senha incorreta".

`[Roadmap]` Multi-usuário com permissões granulares (sócio, caixa, garçom).

---

### 8.2 Dashboard (Home) `[MVP]`

Tela inicial pós-login. Visão executiva do dia/mês.

#### Layout

```
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│  │ FATURAMENTO│ │   TICKET   │ │  COMANDAS  │ │   LUCRO    │     │
│  │  R$ 2.340  │ │ MÉDIO R$78 │ │ABERTAS  12 │ │ ESTIMADO   │     │
│  │   (hoje)   │ │   (hoje)   │ │ FECHADAS 30│ │  R$ 1.450  │     │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│                                                                   │
│  ┌─────────────────────────────────┐ ┌─────────────────────────┐ │
│  │  FATURAMENTO POR HORA (HOJE)    │ │ TOP 10 PRODUTOS         │ │
│  │  [gráfico de barras]            │ │ [gráfico horizontal]    │ │
│  └─────────────────────────────────┘ └─────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────┐ ┌─────────────────────────┐ │
│  │  ÚLTIMOS 30 DIAS                │ │ CALENDÁRIO DO MÊS       │ │
│  │  [gráfico de linha]             │ │ [heatmap de faturamento]│ │
│  └─────────────────────────────────┘ └─────────────────────────┘ │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  COMANDAS ABERTAS                                           │ │
│  │  ┌───────┬─────────────┬────────┬──────────┬──────────────┐ │ │
│  │  │ #001  │ João (M.5)  │ 3 itens│ R$ 87,00 │ há 1h20min   │ │ │
│  │  │ #002  │ Mesa 8      │ 5 itens│ R$143,50 │ há 45min     │ │ │
│  │  └───────┴─────────────┴────────┴──────────┴──────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

#### Componentes

**Cards de indicadores (topo):**
- Faturamento (hoje)
- Ticket médio (hoje)
- Comandas (abertas / fechadas hoje)
- Lucro estimado (hoje, baseado em CMV)

**Gráficos:**
- Faturamento por hora (hoje) — barras
- Top 10 produtos vendidos — barras horizontais
- Últimos 30 dias — linha
- Calendário do mês — heatmap (cada dia colorido por intensidade de faturamento)

**Lista de comandas abertas:**
- Atalho rápido: clicar abre a comanda em modo de lançamento.

`[Pós-MVP]` Alertas no topo (estoque baixo, comanda antiga, produtos sem custo cadastrado).

---

### 8.3 Comandas (Núcleo Operacional)

#### 8.3.1 Tela: Lista de Comandas Abertas `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  COMANDAS ABERTAS                            [+ NOVA COMANDA]    │
│                                                                  │
│  🔍 [Buscar por nome ou mesa...]                                 │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ #001  João (Mesa 5)                              R$ 87,00 │  │
│  │ Garçom: Pedro · 3 itens · aberta há 1h20min                │  │
│  │                                            [Abrir comanda] │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ #002  Mesa 8                                    R$ 143,50 │  │
│  │ Garçom: Ana · 5 itens · aberta há 45min                    │  │
│  │                                            [Abrir comanda] │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ #003  Festa do João                             R$ 412,00 │  │
│  │ Garçom: Pedro · 14 itens · aberta há 2h05min               │  │
│  │                                            [Abrir comanda] │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- Busca por nome ou mesa.
- Cada card mostra: identificação, garçom, qtde itens, valor parcial, tempo aberta.
- Botão `[+ NOVA COMANDA]` no topo direito.
- Clique no card abre tela de lançamento.

---

#### 8.3.2 Tela: Nova Comanda `[MVP]`

Modal sobreposto à lista.

```
┌─────────────────────────────────────────┐
│  NOVA COMANDA                       [✕] │
├─────────────────────────────────────────┤
│                                         │
│  Identificação:                         │
│  (•) Nome do responsável                │
│  ( ) Número da mesa                     │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Ex: João da mesa do canto       │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Garçom responsável:                    │
│  ┌─────────────────────────────────┐    │
│  │ Selecione...                  ▼ │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Pessoas (opcional):                    │
│  ┌──────────────┐ ┌──────────────┐     │
│  │ João         │ │ + Adicionar  │     │
│  └──────────────┘ └──────────────┘     │
│  ┌──────────────┐                      │
│  │ Maria        │                      │
│  └──────────────┘                      │
│                                         │
│              [CANCELAR]  [ABRIR COMANDA]│
└─────────────────────────────────────────┘
```

**Fluxo:**
1. Escolhe identificação (nome ou mesa).
2. Seleciona garçom obrigatório (lista vinda de Cadastros).
3. Pode adicionar pessoas que vão consumir (ex: João, Maria, Pedro) — útil pra associar itens depois.
4. Clica `[ABRIR COMANDA]` → vai pra tela de lançamento.

---

#### 8.3.3 Tela: Comanda Aberta (Lançamento) `[MVP]`

A tela mais usada do sistema. Coração da operação.

```
┌──────────────────────────────────────────────────────────────────┐
│  COMANDA #001 — JOÃO (Mesa 5)            Garçom: Pedro           │
│  Aberta há 1h20min                       [Editar comanda]        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────┐  ┌────────────────────┐    │
│  │  ADICIONAR ITEM                  │  │  ITENS LANÇADOS    │    │
│  │                                  │  │                    │    │
│  │  🔍 [Buscar produto...]          │  │ 2x Coca Lata       │    │
│  │                                  │  │   Para: João       │    │
│  │  Atalhos:                        │  │   R$ 16,00         │    │
│  │  [Coca Lata] [Heineken]          │  │   [Editar][✕]      │    │
│  │  [X-Burguer] [Porção Fritas]     │  │                    │    │
│  │  [Caipirinha] [Água]             │  │ 1x X-Burguer       │    │
│  │                                  │  │   Para: Maria      │    │
│  │  ──────────────────────          │  │   Obs: sem cebola  │    │
│  │  Item selecionado:               │  │   R$ 28,00         │    │
│  │  ┌─────────────────────────┐     │  │   [Editar][✕]      │    │
│  │  │ X-Burguer · R$ 28,00    │     │  │                    │    │
│  │  └─────────────────────────┘     │  │ 1x Heineken        │    │
│  │                                  │  │   Para: João       │    │
│  │  Quantidade: [-] 1 [+]           │  │   🎁 CORTESIA      │    │
│  │                                  │  │   R$ 0,00          │    │
│  │  Para quem? (opcional):          │  │   [Editar][✕]      │    │
│  │  (•) João  ( ) Maria  ( ) Sem    │  │                    │    │
│  │                                  │  │ ────────────────── │    │
│  │  Observação:                     │  │ Subtotal: R$ 44,00 │    │
│  │  ┌─────────────────────────┐     │  │                    │    │
│  │  │ ex: sem cebola          │     │  │                    │    │
│  │  └─────────────────────────┘     │  │                    │    │
│  │                                  │  │                    │    │
│  │  [ ] Cortesia (preço zero)       │  │                    │    │
│  │                                  │  │                    │    │
│  │       [+ ADICIONAR ITEM]         │  │                    │    │
│  └──────────────────────────────────┘  └────────────────────┘    │
│                                                                  │
│   [DESCONTO]   [CANCELAR COMANDA]              [FECHAR CONTA] →  │
└──────────────────────────────────────────────────────────────────┘
```

**Painel esquerdo — Adicionar Item:**
- Busca por nome com autocomplete.
- Atalhos visuais para os 6 produtos mais vendidos (auto-atualizados).
- Após selecionar item, preenche quantidade, pessoa associada, observação, e flag de cortesia.
- Botão `[+ ADICIONAR ITEM]` joga pro painel direito.

**Painel direito — Itens Lançados:**
- Cada linha mostra: quantidade × nome, pessoa, observação, valor, ações.
- Item com 🎁 = cortesia (preço zero).
- Botão `[Editar]` permite alterar quantidade, pessoa, obs.
- Botão `[✕]` cancela o item (com confirmação e pergunta sobre estorno de estoque).

**Ações inferiores:**
- `[DESCONTO]` — abre modal pra aplicar desconto na comanda toda (% ou valor).
- `[CANCELAR COMANDA]` — destrutivo, requer confirmação.
- `[FECHAR CONTA]` — vai pra tela de fechamento.

---

#### 8.3.4 Modal: Cancelar Item `[MVP]`

Disparado ao clicar `[✕]` em um item da comanda.

```
┌──────────────────────────────────────────┐
│  CANCELAR ITEM?                      [✕] │
├──────────────────────────────────────────┤
│                                          │
│  Item: 1x X-Burguer (Maria)              │
│  Valor: R$ 28,00                         │
│                                          │
│  Motivo do cancelamento:                 │
│  ┌──────────────────────────────────┐    │
│  │ Selecione...                   ▼ │    │
│  │  · Cliente desistiu              │    │
│  │  · Erro de lançamento            │    │
│  │  · Item indisponível             │    │
│  │  · Outro                         │    │
│  └──────────────────────────────────┘    │
│                                          │
│  [ ] Estornar itens ao estoque           │
│      (marque se o produto não foi        │
│       preparado/aberto)                  │
│                                          │
│              [VOLTAR]  [CONFIRMAR]       │
└──────────────────────────────────────────┘
```

---

#### 8.3.5 Modal: Aplicar Desconto `[MVP]`

```
┌────────────────────────────────────────┐
│  APLICAR DESCONTO                  [✕] │
├────────────────────────────────────────┤
│                                        │
│  Subtotal atual: R$ 143,50             │
│                                        │
│  Tipo de desconto:                     │
│  (•) Percentual    ( ) Valor fixo      │
│                                        │
│  ┌──────────────┐                      │
│  │ 10         % │                      │
│  └──────────────┘                      │
│                                        │
│  Novo total: R$ 129,15                 │
│                                        │
│              [CANCELAR]  [APLICAR]     │
└────────────────────────────────────────┘
```

---

#### 8.3.6 Tela: Fechamento de Comanda `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  FECHAR COMANDA #001 — JOÃO (Mesa 5)                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  RESUMO                                                    │  │
│  │                                                            │  │
│  │  2x Coca Lata          (João)              R$  16,00       │  │
│  │  1x X-Burguer          (Maria) sem cebola  R$  28,00       │  │
│  │  1x Heineken           (João)  🎁 cortesia R$   0,00       │  │
│  │  3x Porção Fritas                          R$  45,00       │  │
│  │                                                            │  │
│  │  Subtotal:                                 R$  89,00       │  │
│  │  Desconto (10%):                          -R$   8,90       │  │
│  │  ────────────────────────────────────────────────────      │  │
│  │  TOTAL:                                    R$  80,10       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  COMO DIVIDIR?                                                   │
│  (•) Sem divisão (paga tudo)                                     │
│  ( ) Dividir igualmente entre N pessoas                          │
│  ( ) Cada pessoa paga um valor diferente                         │
│  ( ) Pagamento parcial (comanda continua aberta)                 │
│                                                                  │
│  PAGAMENTO:                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Método:        Valor:                                   │   │
│  │  [PIX       ▼]  [R$ 50,10]              [+ Adicionar]    │   │
│  │  [Crédito   ▼]  [R$ 30,00]              [✕]              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Total recebido: R$ 80,10 ✓                                      │
│                                                                  │
│   [VOLTAR]                              [CONFIRMAR FECHAMENTO]   │
└──────────────────────────────────────────────────────────────────┘
```

**Modos de divisão:**

| Modo | Comportamento |
|------|---------------|
| Sem divisão | Total cheio, um pagamento (ou misto) |
| Dividir igualmente | Pergunta N pessoas, divide o total por N, mostra valor por pessoa |
| Valor diferente por pessoa | Lista as pessoas vinculadas, cada uma com campo de valor; soma deve bater com total |
| Pagamento parcial | Cliente paga X agora, comanda volta pra estado aberta com saldo restante |

**Pagamento misto:**
- Pode adicionar várias linhas de pagamento (PIX + Crédito + Dinheiro).
- Sistema valida se a soma bate com o total a pagar.

**Ao confirmar fechamento:**
1. Comanda muda status pra `fechada`.
2. Estoque é abatido (todos os itens não-cancelados).
3. Toast verde "Comanda fechada com sucesso".
4. Vai pra tela de Comprovante.

---

#### 8.3.7 Tela: Comprovante `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  COMPROVANTE — COMANDA #001                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────┐                  │
│  │   ESTAÇÃO MATCHPOINT                       │                  │
│  │   12/05/2026 22:34                         │                  │
│  │   Comanda #001 — João (Mesa 5)             │                  │
│  │                                            │                  │
│  │   2x Coca Lata           R$ 16,00          │                  │
│  │   1x X-Burguer           R$ 28,00          │                  │
│  │   1x Heineken (cortesia) R$  0,00          │                  │
│  │   3x Porção Fritas       R$ 45,00          │                  │
│  │                                            │                  │
│  │   Subtotal:              R$ 89,00          │                  │
│  │   Desconto:             -R$  8,90          │                  │
│  │   TOTAL:                 R$ 80,10          │                  │
│  │                                            │                  │
│  │   PIX:                   R$ 50,10          │                  │
│  │   Crédito:               R$ 30,00          │                  │
│  │                                            │                  │
│  │   *** NÃO É CUPOM FISCAL ***               │                  │
│  └────────────────────────────────────────────┘                  │
│                                                                  │
│         [IMPRIMIR]    [VOLTAR ÀS COMANDAS]                       │
└──────────────────────────────────────────────────────────────────┘
```

**Ao clicar `[IMPRIMIR]`:**
- `[MVP]` Abre o diálogo de impressão do navegador (Ctrl+P). Operador escolhe a impressora Obitech WD-80R7 e confirma.
- `[Pós-MVP]` Helper desktop ou impressão via rede direta — sem diálogo.

`[Confirmar]` Cupom fiscal (NFCe) — depende de validação com cliente, certificado digital, integração SEFAZ. Tratado como módulo separado pós-contrato.

---

### 8.4 Compras

#### 8.4.1 Tela: Lista de Compras `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  COMPRAS                          [+ NOVA COMPRA]                │
│                                                                  │
│  Filtros: [Período ▼] [Fornecedor ▼]                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ 03/05/2026  Bebidas Brasil                  R$  1.240,00   │  │
│  │ Nota: 12345 · 4 itens                       [Ver detalhes] │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 28/04/2026  Açougue do Bairro               R$    580,00   │  │
│  │ Nota: — · 2 itens                           [Ver detalhes] │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Total no período: R$ 1.820,00                                   │
└──────────────────────────────────────────────────────────────────┘
```

#### 8.4.2 Tela: Nova Compra Manual `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  NOVA COMPRA                                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Fornecedor:    [Selecione...                              ▼]    │
│                 [+ Cadastrar novo fornecedor]                    │
│                                                                  │
│  Data da compra: [03/05/2026]                                    │
│  Número da nota: [_______________] (opcional)                    │
│                                                                  │
│  ITENS COMPRADOS:                                                │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Item                  Qtd      Unidade     Custo Total     │  │
│  │ [Coca Lata        ▼]  [240]    [un]       [R$ 480,00]  [✕] │  │
│  │ [Carne moída      ▼]  [5000]   [g]        [R$ 250,00]  [✕] │  │
│  │ [+ Adicionar item]                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Total da compra: R$ 730,00                                      │
│                                                                  │
│              [CANCELAR]              [SALVAR COMPRA]             │
└──────────────────────────────────────────────────────────────────┘
```

**Ao salvar:**
1. Cada item entra no estoque (soma na quantidade atual).
2. Custo médio é recalculado (média ponderada).
3. Toast verde "Compra registrada".

`[Pós-MVP]` Aba `[IMPORTAR XML]` ao lado de `[+ NOVA COMPRA]` que sobe um XML de NFe e popula tudo automaticamente, com tela de "de-para" pra vincular itens novos.

---

### 8.5 Estoque

#### 8.5.1 Tela: Saldo Atual `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  ESTOQUE                          [BAIXA SEM VENDA] [AJUSTAR]    │
│                                                                  │
│  Filtros: [Categoria ▼] [Tipo: simples/composto ▼] 🔍            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Item                Categoria      Saldo       Custo médio │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Coca Lata           Refrigerantes  240 un      R$ 2,00     │  │
│  │ Heineken Long Neck  Cervejas       144 un      R$ 6,50     │  │
│  │ Carne moída         Carnes       12.450 g      R$ 0,05/g   │  │
│  │ Queijo mussarela    Frios         8.300 g      R$ 0,04/g   │  │
│  │ Pão de hambúrguer   Pães             80 un     R$ 1,20     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

**Observação:** itens compostos (ex: X-Burguer) não aparecem aqui — eles não têm estoque próprio, dependem do estoque dos insumos.

#### 8.5.2 Modal: Baixa Sem Venda `[MVP]`

Disparada pelo botão `[BAIXA SEM VENDA]`.

```
┌────────────────────────────────────────────┐
│  BAIXA SEM VENDA                       [✕] │
├────────────────────────────────────────────┤
│                                            │
│  Item:                                     │
│  ┌──────────────────────────────────────┐  │
│  │ Selecione...                       ▼ │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  Quantidade: [_____]                       │
│                                            │
│  Motivo:                                   │
│  ( ) Consumo interno                       │
│  ( ) Quebra/perda                          │
│  ( ) Cortesia                              │
│  ( ) Outro: [_______________]              │
│                                            │
│  Observação (opcional):                    │
│  ┌──────────────────────────────────────┐  │
│  │                                      │  │
│  └──────────────────────────────────────┘  │
│                                            │
│              [CANCELAR]  [CONFIRMAR]       │
└────────────────────────────────────────────┘
```

#### 8.5.3 Tela: Histórico de Movimentações `[MVP]`

Lista cronológica de todas as movimentações de estoque (entradas, saídas por venda, baixas sem venda, ajustes).

```
┌──────────────────────────────────────────────────────────────────┐
│  HISTÓRICO DE MOVIMENTAÇÕES                                      │
│                                                                  │
│  Filtros: [Item ▼] [Tipo ▼] [Período ▼]                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Data       Item          Tipo            Qtd      Saldo    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ 12/05 22h  Coca Lata     Saída (venda)   -2       238 un   │  │
│  │ 12/05 21h  Heineken      Saída (venda)   -1       143 un   │  │
│  │ 12/05 18h  Carne moída   Baixa s/ venda  -200g   12.250g   │  │
│  │ 12/05 14h  Coca Lata     Entrada         +240    240 un    │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

### 8.6 Cadastros

#### 8.6.1 Tela: Lista de Itens `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  ITENS                              [+ NOVO ITEM]                │
│                                                                  │
│  Filtros:                                                        │
│  Tipo: ( ) Todos  (•) Simples  ( ) Composto                      │
│  [Categoria ▼]  [Vendável: Todos ▼]  🔍                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Nome              Categoria    Tipo     Vendável  Preço    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │ Coca Lata         Refri        Simples  Sim       R$ 8,00  │  │
│  │ Carne moída       Carnes       Simples  Não       —        │  │
│  │ X-Burguer         Lanches      Composto Sim       R$ 28,00 │  │
│  │ Balde 6 LongNeck  Cervejas     Composto Sim       R$ 45,00 │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

#### 8.6.2 Tela: Cadastro/Edição de Item `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  CADASTRAR ITEM                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Nome:        [_______________________________________]          │
│  Categoria:   [Selecione...                       ▼]             │
│                                                                  │
│  Tipo:        (•) Simples (compra direto)                        │
│               ( ) Composto (tem ficha técnica)                   │
│                                                                  │
│  Vendável?    [✓] Sim, aparece como opção em comanda             │
│                                                                  │
│  Unidade:     (•) Unidade (un)                                   │
│               ( ) Massa (g/kg)                                   │
│                                                                  │
│  ┌──── Se "Unidade" ────────────────────────────────────┐        │
│  │  Vem em caixa? [✓] Sim                              │        │
│  │  Quantidade por caixa: [24]                         │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  Preço de venda: [R$ ______]   (só se vendável)                  │
│                                                                  │
│  ── FICHA TÉCNICA (só se Composto) ─────────────────────         │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ Insumo            Quantidade    Unidade               │      │
│  │ [Pão hambúrg.  ▼] [1]           un              [✕]   │      │
│  │ [Carne moída   ▼] [200]         g               [✕]   │      │
│  │ [Queijo        ▼] [50]          g               [✕]   │      │
│  │ [+ Adicionar insumo]                                  │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                  │
│  Custo calculado: R$ 11,30                                       │
│  CMV: 40,4% (R$ 11,30 / R$ 28,00)                                │
│                                                                  │
│              [CANCELAR]                  [SALVAR]                │
└──────────────────────────────────────────────────────────────────┘
```

**Validações:**
- Item composto **deve** ter ao menos 1 insumo na ficha.
- Item não-vendável **não pode** ter preço de venda.
- Item composto não pode ter outro composto na ficha (`[Roadmap]` ficha aninhada).

#### 8.6.3 Tela: Categorias `[MVP]`

CRUD simples. Lista + modal de cadastro/edição com campo único: nome.

#### 8.6.4 Tela: Fornecedores `[MVP]`

CRUD simples. Campos: nome (obrigatório), CNPJ (opcional), contato (opcional).

#### 8.6.5 Tela: Garçons `[MVP]`

CRUD simples. Campos: nome, ativo (boolean).

```
┌────────────────────────────────────────────┐
│  GARÇONS                  [+ NOVO GARÇOM]  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Pedro       Ativo      [Editar][✕]   │  │
│  │ Ana         Ativo      [Editar][✕]   │  │
│  │ Carlos      Inativo    [Editar][✕]   │  │
│  └──────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

#### 8.6.6 Tela: Métodos de Pagamento `[MVP]`

CRUD simples. MVP já vem com PIX, Crédito, Débito, Dinheiro pré-cadastrados. Sócio pode desativar ou adicionar (ex: vale-refeição).

---

### 8.7 Relatórios

Todas as telas seguem o padrão: filtros no topo (período, etc.) + resultado em tabela ou gráfico.

#### 8.7.1 Vendas do Dia `[MVP]`

Lista detalhada de comandas fechadas no dia, com totais, métodos de pagamento e itens.

#### 8.7.2 Histórico de Comandas `[MVP]`

Mesma estrutura, mas com filtro de período aberto (semana, mês, custom). Permite buscar por nome, garçom, mesa.

#### 8.7.3 Fechamento de Caixa `[MVP]`

Tela de conferência ao final do dia/turno.

```
┌──────────────────────────────────────────────────────────────────┐
│  FECHAMENTO DE CAIXA — 12/05/2026                                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Total de comandas fechadas: 30                                  │
│  Faturamento bruto: R$ 2.340,00                                  │
│  Descontos aplicados: R$ 180,00                                  │
│  Cortesias: R$ 75,00                                             │
│  Faturamento líquido: R$ 2.085,00                                │
│                                                                  │
│  POR MÉTODO DE PAGAMENTO:                                        │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ PIX            R$ 1.140,00     14 transações            │    │
│  │ Crédito        R$   620,00      8 transações            │    │
│  │ Débito         R$   240,00      6 transações            │    │
│  │ Dinheiro       R$    85,00      2 transações            │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [EXPORTAR PDF]                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### 8.7.4 DRE Simplificado `[MVP]`

```
┌──────────────────────────────────────────────────────────────────┐
│  DRE SIMPLIFICADO — Maio/2026                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RECEITA                                                         │
│    Faturamento bruto:              R$ 64.500,00                  │
│    (-) Descontos e cortesias:      R$  3.200,00                  │
│    Faturamento líquido:            R$ 61.300,00                  │
│                                                                  │
│  CUSTOS                                                          │
│    Custo das mercadorias (CMV):    R$ 22.800,00                  │
│    Perdas/quebras:                 R$    480,00                  │
│    Total de custos:                R$ 23.280,00                  │
│                                                                  │
│  ────────────────────────────────────────────────                │
│  LUCRO BRUTO:                      R$ 38.020,00                  │
│  Margem:                           62%                           │
└──────────────────────────────────────────────────────────────────┘
```

#### 8.7.5 CMV por Produto `[MVP]`

Lista todos os produtos vendáveis com: preço de venda, custo, margem (R$ e %), classificação visual (verde/amarelo/vermelho).

#### 8.7.6 Perdas e Cortesias `[MVP]`

Lista de baixas sem venda + cortesias aplicadas, agrupadas por motivo, com totais.

#### 8.7.7 Vendas por Garçom `[MVP]`

Ranking dos garçons por faturamento, total de comandas, ticket médio. Útil para o sócio identificar performance e padrões suspeitos (muitas cortesias, cancelamentos).

---

### 8.8 Configurações

#### 8.8.1 Dados do Estabelecimento `[MVP]`

Nome fantasia, CNPJ, endereço, telefone. Aparece no comprovante.

#### 8.8.2 Senha `[MVP]`

Alteração da senha única do sistema.

#### 8.8.3 Impressora `[MVP]`

Tela informativa: instruções para configurar a Obitech WD-80R7 no sistema operacional. Sem integração técnica no MVP (impressão via diálogo do navegador).

`[Pós-MVP]` Configuração direta da impressora (USB ou IP de rede), teste de impressão, layout customizável do comprovante.

#### 8.8.4 Backup/Exportação `[MVP]`

Botão para exportar todos os dados em formato JSON ou Excel. Operação manual sob demanda.

`[Pós-MVP]` Backup automático em nuvem.

---

## 9. Casos de Borda e Validações

### 9.1 Comanda

| Cenário | Comportamento |
|---------|---------------|
| Cliente sai sem pagar | Comanda permanece aberta. Após X horas, alerta no dashboard. `[Pós-MVP]` Mecanismo formal de "comanda perdida". |
| Garçom inativado com comanda aberta | Comanda continua válida. Histórico mantém o nome do garçom. |
| Item excluído do cadastro com comanda em aberto | Item da comanda permanece (snapshot do preço). Mas não aparece mais como opção de novo lançamento. |
| Estoque insuficiente no fechamento | Toast amarelo de aviso, mas permite fechar. Saldo fica negativo. `[Pós-MVP]` Configuração para bloquear ou só avisar. |
| Internet cair durante operação | `[MVP]` operação interrompida. `[Roadmap]` modo offline com sincronização posterior. |
| Duas pessoas abrem mesma comanda simultaneamente | Last-write-wins no MVP (último a salvar sobrescreve). `[Pós-MVP]` Lock otimista com aviso. |

### 9.2 Estoque

| Cenário | Comportamento |
|---------|---------------|
| Saldo negativo | Permitido, com toast amarelo. Sócio pode ajustar manualmente. |
| Item composto sem insumo cadastrado | Bloqueia salvamento da ficha técnica. |
| Custo médio com primeira compra | Custo médio = custo da compra. |
| Item sem custo cadastrado | CMV não é calculado, aparece como "—" nos relatórios. |

### 9.3 Pagamento

| Cenário | Comportamento |
|---------|---------------|
| Soma dos pagamentos não bate com total | Bloqueia o `[CONFIRMAR FECHAMENTO]`. |
| Pagamento parcial | Comanda volta a "aberta", saldo restante = total - parcial. |
| Reabrir comanda fechada | Modal de confirmação. Estoque é estornado dos itens. Status muda para "reaberta". |

### 9.4 Reabertura de Comanda

`[MVP]` Tela de detalhes da comanda fechada (a partir do histórico) tem botão `[REABRIR]`. Confirma, estorna estoque, comanda volta ao fluxo de lançamento normal. Histórico marca como "reaberta" e registra evento.

Reabertura só é possível em comandas com status `fechada`. Comandas em pagamento parcial estão em estado `aberta com saldo pendente` e não exigem reabertura — basta lançar/fechar normalmente.

### 9.5 Lógica de Negócio — Decisões Adicionais

| Cenário | Regra |
|---------|-------|
| Cortesia e CMV | Cortesia é registrada no CMV (custo do insumo consumido) mas não em receita. Aparece como dedução em "Perdas e Cortesias" e no DRE. |
| Desconto + pagamento parcial | Desconto fica pendente até o fechamento total. Pagamento parcial é calculado sobre o subtotal **sem** desconto. |
| Edição de item em comanda aberta | Estoque só é baixado no fechamento. Edição livre de qtd/pessoa/observação enquanto comanda aberta — nenhum efeito no estoque. |
| Item composto sem estoque suficiente | Mesma regra do simples: explode ficha técnica, baixa cada insumo, permite saldo negativo, toast amarelo lista insumos negativos. |
| Custo médio com estoque ≤ 0 | Se `estoque_anterior <= 0`, custo médio é **redefinido** para o custo unitário da nova compra (reseta), em vez de aplicar média ponderada. |
| Divisão "valor diferente por pessoa" | Bloqueada se a comanda tiver < 2 pessoas cadastradas. Toast orienta cadastrar pessoas no painel da comanda. |
| Numeração de comandas | MVP exibe `#001` formatando o `id` PK com zero-pad no frontend. Sequencial real fica para pós-MVP. |
| Soft delete de itens | Item referenciado (em ficha técnica ou histórico de comanda) só pode ser desativado (`ativo=false`), nunca removido fisicamente. |
| Garçom inativado mid-comanda | Comanda continua válida; relatórios mantêm o nome no snapshot. |
| Item excluído com comanda aberta referenciando | Snapshot do preço já está em `ItemComanda`. Item some das opções de novo lançamento; comanda existente permanece intacta. |
| Vendas por garçom | Garçom vinculado na **abertura** é o responsável para todos os relatórios. Trocar fechador não muda atribuição. |
| DRE com produto sem custo | Mostra alerta no topo "X produtos sem custo cadastrado, CMV pode estar subestimado. [Ver lista]". Não bloqueia geração. |
| Edição de pessoas em comanda aberta | Sempre editável. Não retroage em itens já associados (snapshot mantido em `pessoa_associada`). |

---

## 10. Arquitetura Técnica (Deep Models)

### 10.1 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                       │
│                         (Vercel - Free)                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              React + Vite + TailwindCSS                   │ │
│  │                                                           │ │
│  │   • Componentes reutilizáveis (botões grandes, modais)    │ │
│  │   • UI simples e intuitiva                                │ │
│  │   • Atalhos visuais para produtos mais vendidos           │ │
│  │   • Toasts para feedback (sucesso/erro/aviso)             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ HTTPS / REST API (JSON)
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   BACKEND ENGINE (Railway)                      │
│                  Python + FastAPI + PostgreSQL                  │
│                      (~R$25-35/mês)                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │       CAMADA DE APRESENTAÇÃO (Controllers/Routes)        │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┬────────┐  │  │
│  │  │  Auth    │ Comandas │ Compras  │ Estoque  │ Itens  │  │  │
│  │  ├──────────┼──────────┼──────────┼──────────┼────────┤  │  │
│  │  │Categorias│Fornece-  │ Garçons  │Pagamentos│Relató- │  │  │
│  │  │          │  dores   │          │          │ rios   │  │  │
│  │  └──────────┴──────────┴──────────┴──────────┴────────┘  │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                     │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │           CAMADA DE NEGÓCIO (Services)                   │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ • Validações complexas (ficha técnica, CMV)      │    │  │
│  │  │ • Cálculo de custo médio (média ponderada)       │    │  │
│  │  │ • Orquestração de transações ACID                │    │  │
│  │  │ • Regras de negócio (cortesia, desconto, divisão)│    │  │
│  │  │ • Lógica de fechamento de comanda                │    │  │
│  │  │ • Baixa de estoque (com explosão de compostos)   │    │  │
│  │  │ • Cálculos de relatórios (DRE, CMV, fechamento)  │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                     │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │           CAMADA DE DADOS (Repositories)                 │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ • Queries SQL otimizadas                         │    │  │
│  │  │ • CRUD por entidade                              │    │  │
│  │  │ • Transações ACID                                │    │  │
│  │  │ • Filtros e agregações                           │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                     │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │       CAMADA DE DOMÍNIO (Models SQLAlchemy + DTOs)       │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │ • Models: Item, Comanda, ItemComanda, Compra,    │    │  │
│  │  │   Fornecedor, Garcom, FichaTecnica,              │    │  │
│  │  │   MovimentoEstoque, Pagamento, Categoria         │    │  │
│  │  │ • DTOs Pydantic para entrada/saída               │    │  │
│  │  │ • Validações básicas (tipos, formatos)           │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                     │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │                    BANCO DE DADOS                        │  │
│  │                      PostgreSQL                          │  │
│  │                                                          │  │
│  │  • Backups automáticos diários                           │  │
│  │  • Transações ACID                                       │  │
│  │  • Conexões simultâneas (20-100)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Detalhamento das Camadas

#### 10.2.1 Camada de Apresentação (Controllers/Routes)

**Responsabilidade:** Receber requisições HTTP, validar inputs básicos via Pydantic, delegar para Services e retornar respostas.

```python
# src/api/routes/comandas.py
from fastapi import APIRouter, Depends, HTTPException
from src.services.comanda_service import ComandaService
from src.schemas.comanda_schemas import (
    ComandaCreate, ComandaResponse, LancarItemRequest, FecharComandaRequest
)

router = APIRouter(prefix="/api/comandas", tags=["comandas"])

@router.post("/", response_model=ComandaResponse)
async def abrir_comanda(
    dados: ComandaCreate,
    service: ComandaService = Depends()
):
    """Abre uma nova comanda (por nome ou mesa)."""
    try:
        return await service.abrir_comanda(dados)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{comanda_id}/itens", response_model=ComandaResponse)
async def lancar_item(
    comanda_id: int,
    item: LancarItemRequest,
    service: ComandaService = Depends()
):
    """Lança um item em uma comanda aberta."""
    try:
        return await service.lancar_item(comanda_id, item)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{comanda_id}/fechar", response_model=ComandaResponse)
async def fechar_comanda(
    comanda_id: int,
    dados: FecharComandaRequest,
    service: ComandaService = Depends()
):
    """Fecha uma comanda, registra pagamento e dá baixa no estoque."""
    try:
        return await service.fechar_comanda(comanda_id, dados)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Características:**
- ❌ **NÃO contém** lógica de negócio
- ❌ **NÃO acessa** diretamente o banco de dados
- ✅ **Apenas:** valida entrada, chama Service, retorna resposta
- ✅ **Thin controllers** — magros e simples

#### 10.2.2 Camada de Negócio (Services)

**Responsabilidade:** Implementar TODA a lógica de negócio do sistema Matchpoint, orquestrar transações e validações complexas.

```python
# src/services/comanda_service.py
from decimal import Decimal
from src.repositories.comanda_repository import ComandaRepository
from src.repositories.item_repository import ItemRepository
from src.repositories.estoque_repository import EstoqueRepository
from src.repositories.pagamento_repository import PagamentoRepository
from src.schemas.comanda_schemas import (
    ComandaCreate, LancarItemRequest, FecharComandaRequest
)

class ComandaService:
    def __init__(
        self,
        comanda_repo: ComandaRepository,
        item_repo: ItemRepository,
        estoque_repo: EstoqueRepository,
        pagamento_repo: PagamentoRepository
    ):
        self.comanda_repo = comanda_repo
        self.item_repo = item_repo
        self.estoque_repo = estoque_repo
        self.pagamento_repo = pagamento_repo

    async def abrir_comanda(self, dados: ComandaCreate):
        """Abre nova comanda com validações de negócio."""

        # Validação: garçom deve estar ativo
        garcom = await self.comanda_repo.buscar_garcom(dados.garcom_id)
        if not garcom or not garcom.ativo:
            raise ValueError("Garçom inativo ou inexistente")

        # Validação: identificação obrigatória
        if not dados.identificacao or not dados.identificacao.strip():
            raise ValueError("Identificação obrigatória (nome ou mesa)")

        return await self.comanda_repo.criar(dados)

    async def lancar_item(self, comanda_id: int, item: LancarItemRequest):
        """Lança item em comanda. Aceita cortesia e observação."""

        comanda = await self.comanda_repo.buscar_por_id(comanda_id)
        if not comanda:
            raise ValueError("Comanda não encontrada")
        if comanda.status != "aberta":
            raise ValueError("Não é possível lançar itens em comanda fechada")

        produto = await self.item_repo.buscar_por_id(item.item_id)
        if not produto or not produto.vendavel:
            raise ValueError("Item não vendável ou inexistente")

        # Snapshot do preço (cortesia = 0)
        preco_unitario = Decimal("0") if item.cortesia else produto.preco_venda

        return await self.comanda_repo.adicionar_item(
            comanda_id=comanda_id,
            item_id=item.item_id,
            quantidade=item.quantidade,
            preco_unitario=preco_unitario,
            pessoa_associada=item.pessoa_associada,
            observacao=item.observacao,
            cortesia=item.cortesia,
        )

    async def fechar_comanda(self, comanda_id: int, dados: FecharComandaRequest):
        """
        Fecha comanda — operação crítica.

        Garante atomicidade entre:
        1. Atualização do status
        2. Registro dos pagamentos
        3. Baixa do estoque (com explosão de compostos via ficha técnica)
        4. Aplicação de desconto/cortesias
        """

        comanda = await self.comanda_repo.buscar_por_id(comanda_id)
        if not comanda:
            raise ValueError("Comanda não encontrada")
        if comanda.status == "fechada":
            raise ValueError("Comanda já está fechada")

        # 1. Calcular subtotal (ignorando itens cancelados e cortesias)
        subtotal = sum(
            i.subtotal for i in comanda.itens
            if not i.cancelado and not i.cortesia
        )

        # 2. Aplicar desconto, se houver
        total = subtotal
        if dados.desconto_percentual:
            total = subtotal * (Decimal("1") - dados.desconto_percentual / Decimal("100"))
        elif dados.desconto_valor:
            total = subtotal - dados.desconto_valor

        # 3. Validar pagamentos (suporte a pagamento misto)
        total_pago = sum(p.valor for p in dados.pagamentos)

        # Pagamento parcial: comanda volta a aberta com saldo restante
        if dados.pagamento_parcial:
            if total_pago >= total:
                raise ValueError("Pagamento parcial deve ser menor que o total")
        else:
            if abs(total_pago - total) > Decimal("0.01"):
                raise ValueError(
                    f"Soma dos pagamentos (R${total_pago}) não bate com total (R${total})"
                )

        # 4. Transação atômica
        async with self.comanda_repo.transacao():
            # Registrar pagamentos
            for pgto in dados.pagamentos:
                await self.pagamento_repo.registrar(
                    comanda_id=comanda_id,
                    metodo=pgto.metodo,
                    valor=pgto.valor,
                )

            if dados.pagamento_parcial:
                # Comanda continua aberta, mas com saldo deduzido
                await self.comanda_repo.atualizar_saldo_pendente(
                    comanda_id, total - total_pago
                )
            else:
                # Fechar comanda
                await self.comanda_repo.fechar(
                    comanda_id=comanda_id,
                    total=total,
                    desconto_percentual=dados.desconto_percentual,
                    desconto_valor=dados.desconto_valor,
                )

                # Dar baixa no estoque (com explosão de compostos)
                for item in comanda.itens:
                    if item.cancelado:
                        continue
                    await self._dar_baixa_estoque(
                        item_id=item.item_id,
                        quantidade=item.quantidade,
                    )

        return await self.comanda_repo.buscar_por_id(comanda_id)

    async def _dar_baixa_estoque(self, item_id: int, quantidade: Decimal):
        """
        Lógica central: itens compostos explodem na ficha técnica.

        Exemplo: vender 1 X-Burguer dá baixa em:
          - 1 pão de hambúrguer
          - 200g de carne moída
          - 50g de queijo
        """
        produto = await self.item_repo.buscar_por_id(item_id)

        if produto.tipo == "simples":
            await self.estoque_repo.dar_baixa_venda(
                produto_id=item_id,
                quantidade=quantidade,
            )
        elif produto.tipo == "composto":
            ficha = await self.item_repo.buscar_ficha_tecnica(item_id)
            for componente in ficha.componentes:
                qtd_total = componente.quantidade * quantidade
                # Recursão: insumo composto cairia aqui (Roadmap)
                await self.estoque_repo.dar_baixa_venda(
                    produto_id=componente.insumo_id,
                    quantidade=qtd_total,
                )

    async def cancelar_item(
        self, comanda_id: int, item_comanda_id: int,
        motivo: str, estornar_estoque: bool
    ):
        """Cancela item da comanda. Pode estornar ou não ao estoque."""
        item = await self.comanda_repo.buscar_item_comanda(item_comanda_id)
        if not item:
            raise ValueError("Item não encontrado na comanda")

        await self.comanda_repo.marcar_item_cancelado(
            item_comanda_id, motivo, estornar_estoque
        )

        # Estornar estoque só se item já tinha sido baixado (comanda fechada)
        # No MVP, baixa só acontece no fechamento, então estorno só na reabertura
        return await self.comanda_repo.buscar_por_id(comanda_id)

    async def reabrir_comanda(self, comanda_id: int):
        """Reabre comanda fechada e estorna estoque dos itens consumidos."""
        comanda = await self.comanda_repo.buscar_por_id(comanda_id)
        if not comanda or comanda.status != "fechada":
            raise ValueError("Comanda não está fechada")

        async with self.comanda_repo.transacao():
            await self.comanda_repo.atualizar_status(comanda_id, "reaberta")

            # Estornar estoque (entrada negativa de venda)
            for item in comanda.itens:
                if item.cancelado:
                    continue
                await self._estornar_estoque(item.item_id, item.quantidade)

        return await self.comanda_repo.buscar_por_id(comanda_id)
```

**Outros Services principais:**

| Service | Responsabilidades |
|---------|-------------------|
| `ItemService` | Cadastro de itens, validação de ficha técnica, cálculo de custo de compostos, validação de tipo simples/composto |
| `CompraService` | Registrar compras, recalcular custo médio (média ponderada), atualizar estoque |
| `EstoqueService` | Baixa sem venda (consumo/perda/cortesia), histórico de movimentações, ajustes manuais |
| `RelatorioService` | DRE, CMV por produto, fechamento de caixa, vendas por garçom, perdas e cortesias |
| `AuthService` | Validação da senha única, geração de sessão (JWT simples no MVP) |

**Características da camada:**
- ✅ **Concentra TODA** a lógica de negócio do Matchpoint
- ✅ **Orquestra** múltiplos Repositories
- ✅ **Garante** transações atômicas (fechamento de comanda + baixa estoque)
- ✅ **Centraliza** cálculos críticos (CMV, custo médio, explosão de compostos)
- ❌ **NÃO acessa** diretamente o banco (sempre via Repositories)

#### 10.2.3 Camada de Dados (Repositories)

**Responsabilidade:** Acesso ao banco de dados, queries SQL, transações ACID.

```python
# src/repositories/comanda_repository.py
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.comanda import Comanda, ItemComanda
from src.schemas.comanda_schemas import ComandaCreate

class ComandaRepository:
    def __init__(self, db: Session):
        self.db = db

    async def criar(self, dados: ComandaCreate) -> Comanda:
        """Insere nova comanda no banco."""
        comanda = Comanda(
            identificacao=dados.identificacao,
            tipo_identificacao=dados.tipo_identificacao,
            garcom_id=dados.garcom_id,
            status="aberta",
            data_abertura=datetime.now(),
        )
        self.db.add(comanda)
        self.db.commit()
        self.db.refresh(comanda)
        return comanda

    async def buscar_por_id(self, comanda_id: int):
        return self.db.query(Comanda).filter(
            Comanda.id == comanda_id
        ).first()

    async def listar_abertas(self):
        return self.db.query(Comanda).filter(
            Comanda.status == "aberta"
        ).order_by(Comanda.data_abertura.desc()).all()

    async def adicionar_item(self, comanda_id, item_id, quantidade,
                              preco_unitario, pessoa_associada,
                              observacao, cortesia):
        item = ItemComanda(
            comanda_id=comanda_id,
            item_id=item_id,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            pessoa_associada=pessoa_associada,
            observacao=observacao,
            cortesia=cortesia,
        )
        self.db.add(item)
        self.db.commit()
        return await self.buscar_por_id(comanda_id)

    async def fechar(self, comanda_id, total, desconto_percentual, desconto_valor):
        comanda = self.db.query(Comanda).filter(Comanda.id == comanda_id).first()
        comanda.status = "fechada"
        comanda.total = total
        comanda.desconto_percentual = desconto_percentual
        comanda.desconto_valor = desconto_valor
        comanda.data_fechamento = datetime.now()
        self.db.commit()
        return comanda

    def transacao(self):
        return self.db.begin()
```

```python
# src/repositories/estoque_repository.py
from src.models.movimento_estoque import MovimentoEstoque
from src.models.item import Item

class EstoqueRepository:
    def __init__(self, db):
        self.db = db

    async def dar_baixa_venda(self, produto_id, quantidade):
        # Registra movimento
        mov = MovimentoEstoque(
            item_id=produto_id,
            tipo="saida_venda",
            quantidade=-quantidade,
            data=datetime.now(),
        )
        self.db.add(mov)

        # Atualiza saldo
        item = self.db.query(Item).filter(Item.id == produto_id).first()
        item.estoque_atual -= quantidade
        self.db.commit()

    async def dar_baixa_sem_venda(self, produto_id, quantidade, motivo, observacao):
        mov = MovimentoEstoque(
            item_id=produto_id,
            tipo="saida_perda",
            quantidade=-quantidade,
            motivo=motivo,
            observacao=observacao,
            data=datetime.now(),
        )
        self.db.add(mov)

        item = self.db.query(Item).filter(Item.id == produto_id).first()
        item.estoque_atual -= quantidade
        self.db.commit()

    async def registrar_entrada(self, produto_id, quantidade, custo_unitario):
        mov = MovimentoEstoque(
            item_id=produto_id,
            tipo="entrada",
            quantidade=quantidade,
            custo_unitario=custo_unitario,
            data=datetime.now(),
        )
        self.db.add(mov)

        # Atualizar estoque e custo médio (média ponderada)
        item = self.db.query(Item).filter(Item.id == produto_id).first()
        estoque_anterior = item.estoque_atual
        custo_anterior = item.custo_medio or 0

        novo_estoque = estoque_anterior + quantidade
        item.custo_medio = (
            (estoque_anterior * custo_anterior + quantidade * custo_unitario)
            / novo_estoque
        ) if novo_estoque > 0 else custo_unitario
        item.estoque_atual = novo_estoque

        self.db.commit()
```

**Repositories do sistema Matchpoint:**

| Repository | Entidade |
|------------|----------|
| `ItemRepository` | Item, FichaTecnica, Categoria |
| `ComandaRepository` | Comanda, ItemComanda |
| `CompraRepository` | Compra, ItemCompra |
| `EstoqueRepository` | MovimentoEstoque |
| `PagamentoRepository` | Pagamento, MetodoPagamento |
| `FornecedorRepository` | Fornecedor |
| `GarcomRepository` | Garçom |
| `RelatorioRepository` | Queries agregadas para DRE, CMV, fechamento |

**Características:**
- ✅ **Apenas** acesso a dados via SQL/ORM
- ✅ **Queries SQL** otimizadas
- ✅ **Transações ACID**
- ❌ **NÃO contém** lógica de negócio
- ❌ **NÃO faz** validações além das constraints do DB

#### 10.2.4 Camada de Domínio (Models + DTOs)

**Models SQLAlchemy** representam as entidades persistidas:

```python
# src/models/item.py
from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from src.database import Base
import enum

class TipoItem(str, enum.Enum):
    SIMPLES = "simples"
    COMPOSTO = "composto"

class UnidadeBase(str, enum.Enum):
    UNIDADE = "un"
    GRAMA = "g"

class Item(Base):
    __tablename__ = "itens"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    tipo = Column(Enum(TipoItem), nullable=False)
    vendavel = Column(Boolean, default=False)
    unidade_base = Column(Enum(UnidadeBase), nullable=False)
    quantidade_caixa = Column(Integer, nullable=True)
    custo_medio = Column(Numeric(10, 4), nullable=True)
    preco_venda = Column(Numeric(10, 2), nullable=True)
    estoque_atual = Column(Numeric(12, 4), default=0)

    categoria = relationship("Categoria", back_populates="itens")
    ficha_tecnica = relationship(
        "FichaTecnica", back_populates="item_composto", uselist=False
    )
```

```python
# src/models/comanda.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.database import Base
import enum

class StatusComanda(str, enum.Enum):
    ABERTA = "aberta"
    FECHADA = "fechada"
    REABERTA = "reaberta"

class TipoIdentificacao(str, enum.Enum):
    NOME = "nome"
    MESA = "mesa"

class Comanda(Base):
    __tablename__ = "comandas"

    id = Column(Integer, primary_key=True, index=True)
    identificacao = Column(String(100), nullable=False)
    tipo_identificacao = Column(Enum(TipoIdentificacao), nullable=False)
    garcom_id = Column(Integer, ForeignKey("garcons.id"))
    status = Column(Enum(StatusComanda), default=StatusComanda.ABERTA)
    total = Column(Numeric(10, 2), nullable=True)
    desconto_percentual = Column(Numeric(5, 2), nullable=True)
    desconto_valor = Column(Numeric(10, 2), nullable=True)
    data_abertura = Column(DateTime, nullable=False)
    data_fechamento = Column(DateTime, nullable=True)

    garcom = relationship("Garcom")
    itens = relationship("ItemComanda", back_populates="comanda")
    pagamentos = relationship("Pagamento", back_populates="comanda")

class ItemComanda(Base):
    __tablename__ = "itens_comanda"

    id = Column(Integer, primary_key=True)
    comanda_id = Column(Integer, ForeignKey("comandas.id"))
    item_id = Column(Integer, ForeignKey("itens.id"))
    quantidade = Column(Numeric(10, 4), nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)  # snapshot
    pessoa_associada = Column(String(100), nullable=True)
    observacao = Column(String(255), nullable=True)
    cortesia = Column(Boolean, default=False)
    cancelado = Column(Boolean, default=False)
    motivo_cancelamento = Column(String(255), nullable=True)

    comanda = relationship("Comanda", back_populates="itens")
    item = relationship("Item")
```

**DTOs Pydantic** para entrada/saída da API:

```python
# src/schemas/comanda_schemas.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal, List

class ComandaCreate(BaseModel):
    identificacao: str = Field(..., min_length=1, max_length=100)
    tipo_identificacao: Literal["nome", "mesa"]
    garcom_id: int
    pessoas: Optional[List[str]] = []

    @validator("identificacao")
    def validar_identificacao(cls, v):
        if not v.strip():
            raise ValueError("Identificação não pode ser vazia")
        return v.strip()

class LancarItemRequest(BaseModel):
    item_id: int
    quantidade: Decimal = Field(..., gt=0)
    pessoa_associada: Optional[str] = None
    observacao: Optional[str] = None
    cortesia: bool = False

class PagamentoItem(BaseModel):
    metodo: Literal["pix", "credito", "debito", "dinheiro", "outro"]
    valor: Decimal = Field(..., gt=0)

class FecharComandaRequest(BaseModel):
    pagamentos: List[PagamentoItem] = Field(..., min_items=1)
    desconto_percentual: Optional[Decimal] = None
    desconto_valor: Optional[Decimal] = None
    pagamento_parcial: bool = False
    modo_divisao: Literal["sem_divisao", "igual", "diferente", "parcial"] = "sem_divisao"

class ItemComandaResponse(BaseModel):
    id: int
    item_id: int
    nome: str
    quantidade: Decimal
    preco_unitario: Decimal
    subtotal: Decimal
    pessoa_associada: Optional[str]
    observacao: Optional[str]
    cortesia: bool
    cancelado: bool

    class Config:
        from_attributes = True

class ComandaResponse(BaseModel):
    id: int
    identificacao: str
    tipo_identificacao: str
    garcom: str
    status: str
    total: Optional[Decimal]
    data_abertura: datetime
    data_fechamento: Optional[datetime]
    itens: List[ItemComandaResponse]

    class Config:
        from_attributes = True
```

### 10.3 Fluxo de Dados na Arquitetura Deep Models

Exemplo prático: **fechamento de uma comanda do Matchpoint** (operação mais crítica do sistema):

```
Cliente pede para fechar a conta
         ↓
POST /api/comandas/123/fechar
{ "pagamentos": [{"metodo": "pix", "valor": 80.10}],
  "desconto_percentual": 10 }
         ↓
┌────────────────────────────────────────────────────┐
│  CONTROLLER (api/routes/comandas.py)               │
│  • Valida JSON via Pydantic (FecharComandaRequest) │
│  • Extrai dados da requisição                      │
│  • Chama ComandaService.fechar_comanda()           │
└────────────────────┬───────────────────────────────┘
                     ↓
┌────────────────────────────────────────────────────┐
│  SERVICE (services/comanda_service.py)             │
│  • Busca comanda                                   │
│  • Valida se pode fechar (status = aberta)         │
│  • Calcula subtotal (ignora cortesias e canceladas)│
│  • Aplica desconto                                 │
│  • Valida que soma dos pagamentos bate com total   │
│  • Inicia transação atômica:                       │
│    1. Registra cada pagamento                      │
│    2. Marca comanda como fechada                   │
│    3. Para cada item não-cancelado:                │
│       - Se simples: baixa direta no estoque        │
│       - Se composto: explode ficha técnica e baixa │
│         cada insumo proporcionalmente              │
└────────────────────┬───────────────────────────────┘
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ COMANDA      │ │PAGAMENTO │ │ ESTOQUE      │
│ REPOSITORY   │ │REPOSITORY│ │ REPOSITORY   │
│              │ │          │ │              │
│ UPDATE       │ │ INSERT   │ │ INSERT       │
│ comandas     │ │ pagamen- │ │ movimentos_  │
│ SET status = │ │ tos      │ │ estoque      │
│ 'fechada'    │ │          │ │ UPDATE       │
│              │ │          │ │ itens SET    │
│              │ │          │ │ estoque_atual│
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      ↓
            ┌──────────────────┐
            │   POSTGRESQL     │
            │ • ACID guaranteed│
            │ • COMMIT atomic  │
            └──────────────────┘
                      ↓
              Toast verde no frontend:
              "Comanda fechada com sucesso"
                      ↓
              Redireciona pro Comprovante
```

### 10.4 Estrutura de Pastas do Backend

```
backend/
├── src/
│   ├── api/                                # Camada de Apresentação
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── comandas.py                 # /api/comandas
│   │   │   ├── itens.py                    # /api/itens
│   │   │   ├── compras.py                  # /api/compras
│   │   │   ├── estoque.py                  # /api/estoque
│   │   │   ├── categorias.py
│   │   │   ├── fornecedores.py
│   │   │   ├── garcons.py
│   │   │   ├── pagamentos.py
│   │   │   └── relatorios.py
│   │   └── dependencies.py                 # Injeção de Services
│   │
│   ├── services/                           # Camada de Negócio
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── comanda_service.py              # Lógica de comanda + fechamento
│   │   ├── item_service.py                 # Cadastro, ficha técnica, CMV
│   │   ├── compra_service.py               # Compras + custo médio ponderado
│   │   ├── estoque_service.py              # Baixas sem venda, ajustes
│   │   ├── pagamento_service.py            # Validação de pagamento misto
│   │   └── relatorio_service.py            # DRE, CMV, fechamento de caixa
│   │
│   ├── repositories/                       # Camada de Dados
│   │   ├── __init__.py
│   │   ├── base_repository.py              # CRUD genérico
│   │   ├── comanda_repository.py
│   │   ├── item_repository.py              # Inclui FichaTecnica
│   │   ├── compra_repository.py
│   │   ├── estoque_repository.py
│   │   ├── pagamento_repository.py
│   │   ├── categoria_repository.py
│   │   ├── fornecedor_repository.py
│   │   ├── garcom_repository.py
│   │   └── relatorio_repository.py         # Queries agregadas
│   │
│   ├── models/                             # Camada de Domínio (DB Models)
│   │   ├── __init__.py
│   │   ├── item.py                         # Item, FichaTecnica
│   │   ├── comanda.py                      # Comanda, ItemComanda
│   │   ├── compra.py                       # Compra, ItemCompra
│   │   ├── movimento_estoque.py
│   │   ├── pagamento.py                    # Pagamento, MetodoPagamento
│   │   ├── categoria.py
│   │   ├── fornecedor.py
│   │   └── garcom.py
│   │
│   ├── schemas/                            # Camada de Domínio (DTOs)
│   │   ├── __init__.py
│   │   ├── auth_schemas.py
│   │   ├── comanda_schemas.py
│   │   ├── item_schemas.py
│   │   ├── compra_schemas.py
│   │   ├── estoque_schemas.py
│   │   ├── pagamento_schemas.py
│   │   └── relatorio_schemas.py
│   │
│   ├── core/                               # Configurações
│   │   ├── __init__.py
│   │   ├── config.py                       # Variáveis de ambiente
│   │   ├── database.py                     # Conexão PostgreSQL
│   │   └── security.py                     # JWT/senha do MVP
│   │
│   └── main.py                             # Entry point FastAPI
│
├── tests/
│   ├── unit/                               # Testes de Services
│   │   ├── test_comanda_service.py
│   │   ├── test_item_service.py
│   │   └── test_compra_service.py
│   ├── integration/                        # Testes de Repositories
│   └── e2e/                                # Testes de API completa
│
├── alembic/                                # Migrações do banco
│   └── versions/
│
├── requirements.txt
├── .env.example
└── README.md
```

### 10.5 Vantagens da Arquitetura Deep Models para o Matchpoint

| Vantagem | Benefício prático no projeto |
|----------|------------------------------|
| **Separação de responsabilidades** | Código organizado, fácil manutenção durante o mês de teste |
| **Testabilidade** | Cada camada testável isoladamente; lógica crítica (fechamento) tem cobertura |
| **Manutenibilidade** | Ajustes semanais às terças não viram bagunça — mudanças ficam localizadas |
| **Escalabilidade** | Roadmap (delivery, multi-loja, IA) não exige refatoração estrutural |
| **Reusabilidade** | Mesmos Services servirão para futuro app mobile ou integração com PagBank |
| **Lógica centralizada** | Cálculo de CMV, custo médio e explosão de compostos vivem em um único lugar |
| **Transações seguras** | Fechamento de comanda + baixa de estoque não geram inconsistência |

### 10.6 Estrutura do Frontend e Padrões de UI

#### Estrutura de pastas

```
frontend/
├── src/
│   ├── pages/                    # rotas (Login, Dashboard, Comandas, etc.)
│   ├── features/                 # lógica e componentes por feature
│   │   ├── comandas/
│   │   ├── compras/
│   │   ├── estoque/
│   │   ├── cadastros/
│   │   └── relatorios/
│   ├── components/               # UI compartilhado (Button, Modal, Toast, Topbar, Sidebar)
│   ├── hooks/                    # hooks reutilizáveis
│   ├── stores/                   # Zustand stores (sessão, UI global)
│   ├── schemas/                  # Zod schemas (forms + validação)
│   ├── lib/
│   │   ├── api.ts                # axios + interceptors (JWT, erro padrão, 401 → logout)
│   │   ├── format.ts             # formatCurrency, formatDate (Intl.NumberFormat ptBR, date-fns)
│   │   └── sentry.ts             # bootstrap Sentry
│   └── main.tsx                  # entry point
├── public/
├── index.html
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

#### Resolução suportada

- **Mínimo:** 1280×720 (HD).
- Design responsivo via Tailwind, base em `md:` (768px+); split de painéis (Comanda Aberta, Cadastro de Item) ativa em `lg:` (1024px+).
- Densidade reduzida no MVP: padding `p-3`, botões `h-10` (mínimo tátil 40px), atalhos de produtos em grid 3×2 (em vez de 6×1).
- **Não suportado:** viewport <1280px. Mobile entra apenas no roadmap pós-MVP.

#### Roteamento e Auth

- Wrapper `<RequireAuth>` checa JWT em `localStorage` e redireciona para `/login` se ausente/expirado.
- Layout pai (Topbar + Sidebar) envolve rotas autenticadas.
- JWT expira em 12h, sem refresh token no MVP.
- Resposta 401 do backend → interceptor axios limpa storage e força redirect.

#### Atalhos do Lançamento

- Os 6 atalhos visuais da tela de Comanda Aberta vêm de `GET /api/itens/top?dias=7&limit=6` — itens mais vendidos nos últimos 7 dias por quantidade. Cache via TanStack Query (5min).

### 10.7 Padrões Transversais

#### 10.7.1 Concorrência (controle otimista)

- Coluna `version` (int, default 1, NOT NULL) na tabela `comandas`. Cada UPDATE incrementa.
- UPDATE valida `WHERE id=? AND version=?`. Mismatch retorna **409** com código `COMANDA_DESATUALIZADA`.
- Frontend exibe toast vermelho "Comanda alterada por outro usuário, recarregue" e refaz o GET automaticamente.

#### 10.7.2 Timezone

- Persistência em **UTC**. Conversão para `America/Sao_Paulo` na borda da aplicação (entrada/saída).
- Variável de ambiente `TZ=America/Sao_Paulo` no servidor.
- Relatórios "do dia" usam range em horário local convertido para UTC na query.

#### 10.7.3 Padrão de Erros da API

Exception handler global FastAPI retorna sempre o mesmo formato:

```json
{
  "error": {
    "code": "COMANDA_FECHADA",
    "message": "Comanda já fechada",
    "field": null
  }
}
```

- Códigos de erro são constantes enumeradas no backend (ex.: `COMANDA_FECHADA`, `GARCOM_INATIVO`, `PAGAMENTO_NAO_BATE`, `COMANDA_DESATUALIZADA`).
- Frontend faz match para mensagem amigável e destaque de campo (se `field` preenchido).

#### 10.7.4 Migrations e Seeds

- **Alembic** versiona o schema. Cada mudança de model gera revision (`alembic revision --autogenerate -m "..."`).
- `alembic upgrade head` será configurado como etapa pré-deploy (release command no Railway, quando integração for ativada). Em desenvolvimento, dev roda manualmente.
- **Seeds** (`src/seeds.py`) — script idempotente que popula dados iniciais obrigatórios (sem os quais o sistema não funciona): métodos de pagamento (PIX, Crédito, Débito, Dinheiro) e categoria default. Roda 1x ao subir o ambiente.

#### 10.7.5 Logging e Observabilidade

- **structlog** no backend, formato JSON. Cada log tem campos estruturados (`event`, `request_id`, `comanda_id`, `latencia_ms`, etc.).
- Operações com logging obrigatório: boot da aplicação, cada request HTTP, abertura/fechamento de comanda, baixa de estoque, exceptions.
- **Sentry** captura exceptions automaticamente (frontend e backend). DSN via env var. Alerta por email quando erro ocorrer em produção.

#### 10.7.6 Variáveis de Ambiente

Vars (definidas em `.env.example` versionado e validadas via Pydantic `Settings` no boot):

| Var | Descrição |
|-----|-----------|
| `DATABASE_URL` | String de conexão PostgreSQL |
| `JWT_SECRET` | Segredo para assinar tokens |
| `JWT_EXPIRES_HOURS` | Padrão: 12 |
| `TZ` | `America/Sao_Paulo` |
| `CORS_ORIGINS` | Lista de origens permitidas (URL Vercel + localhost) |
| `ENV` | `dev` ou `prod` |
| `SENTRY_DSN_BACKEND` | DSN Sentry do backend |
| `SENTRY_DSN_FRONTEND` | DSN Sentry do frontend |

#### 10.7.7 CORS

- `CORSMiddleware` FastAPI com **allowlist explícita** (sem `*`).
- Inclui URL de produção do frontend + `http://localhost:5173` (dev local).

#### 10.7.8 Health Check

- `GET /health` retorna `{"status":"ok","db":"ok","version":"x.y.z"}` testando conexão com DB.
- Usado por Railway (quando integração ativada) para restart automático.

#### 10.7.9 Backup e Exportação

- Endpoint `GET /api/backup?formato=json|xlsx` autenticado, gera on-demand:
  - **JSON:** dump completo de todas as tabelas.
  - **Excel (.xlsx):** 3 planilhas — comandas, itens, movimento_estoque.
- Operação manual sob demanda no MVP. Backup automático em nuvem entra no roadmap pós-MVP.

#### 10.7.10 Auditoria de Comanda

Tabela `eventos_comanda` registra mudanças de estado de comanda para auditoria:

| Campo | Descrição |
|-------|-----------|
| `id` | PK |
| `comanda_id` | FK |
| `tipo` | enum: `aberta`, `item_lancado`, `item_cancelado`, `descontada`, `fechada`, `reaberta` |
| `payload` | JSONB com snapshot do dado relevante |
| `garcom_id` | FK (nullable em ações de sócio) |
| `timestamp` | UTC |

Alimenta a UI de auditoria pós-MVP. No MVP a tabela já é gravada, sem tela própria de visualização.

### 10.8 Stack Tecnológico — Resumo Completo

#### Frontend
- **React 18** — biblioteca de UI
- **Vite 5** — build tool ultra-rápido
- **TailwindCSS 3** — estilização utility-first (UI simples e óbvia)
- **Axios** — requisições HTTP
- **React Router v6** — navegação entre telas
- **TanStack Query** — server state, cache e refetch automático
- **Zustand** — estado global de UI (sessão, preferências, modais)
- **React Hook Form + Zod** — formulários e validação (schemas espelham os DTOs Pydantic do backend)
- **shadcn/ui** — componentes base copy-paste sobre Tailwind (Button, Dialog, Input, Select, Combobox, Table, Card, Skeleton)
- **sonner** — toasts (sucesso/erro/aviso conforme §5.3.2)
- **date-fns (locale ptBR)** — formatação de datas
- **Sentry (`@sentry/react`)** — captura automática de exceptions em produção

#### Backend (Deep Models Architecture)
- **Python 3.11+** — linguagem
- **FastAPI** — framework web moderno (async, docs automáticas)
- **SQLAlchemy 2.0** — ORM (Models + Repositories)
- **Pydantic v2** — validação de dados (DTOs)
- **Alembic** — migrações de banco
- **Uvicorn** — servidor ASGI

#### Banco de Dados
- **PostgreSQL 15** — banco relacional com transações ACID

#### Hospedagem
- **Vercel** — frontend (gratuito) — *decidido, integração ainda não ativada*
- **Railway** — backend + PostgreSQL (~R$25-35/mês) — *decidido, integração ainda não ativada*

> ⚠️ **Status da hospedagem (06/05/2026):** Vercel e Railway estão definidos como decisão arquitetural, mas a integração técnica e o setup das contas **ainda não foram realizados**. O desenvolvimento e testes ocorrem localmente até a etapa de deploy. Custos só incidem após provisionamento.

#### DevOps
- **Git + GitHub** — versionamento
- **GitHub Actions** (futuro) — CI/CD automatizado
- **Railway CLI** — deploy manual no MVP (a configurar)

#### Observabilidade
- **structlog** (backend) — logs estruturados em JSON
- **Sentry** (frontend + backend) — captura de exceptions, alerta automático (free tier 5k eventos/mês)

---

## 11. Infraestrutura e Hospedagem

### 11.1 Solução Escolhida

**Railway (Backend + PostgreSQL) + Vercel (Frontend)**

#### Railway
- **Função:** Hospedagem do backend FastAPI + banco PostgreSQL
- **Custo:** ~$5/mês (~R$25/mês)
- **Vantagens:**
  - PostgreSQL + Backend no mesmo projeto
  - Deploy automático via Git (push → produção)
  - Não pausa automaticamente
  - Dashboard simples para monitoramento
  - Pay-as-you-go (cobra pelo uso real)

#### Vercel
- **Função:** Hospedagem do frontend React
- **Custo:** **Gratuito** (plano hobby)
- **Vantagens:**
  - Deploy automático via Git
  - CDN global (site rápido)
  - SSL/HTTPS automático
  - Preview deployments para testar antes de publicar

### 11.2 Estrutura de Custos

| Item | Custo Mensal | Observação |
|------|--------------|------------|
| **Railway** (Backend + DB) | R$25-35 | PostgreSQL + FastAPI |
| **Vercel** (Frontend) | R$0 | Gratuito |
| **Domínio** | R$5-8 | .com.br anual ÷ 12 |
| **Buffer/margem** | R$57-70 | Para futuras integrações |
| **TOTAL ESTIMADO** | **~R$35-40/mês** | Bem dentro do orçamento de R$100 |

### 11.3 Como Funciona a Hospedagem do Banco de Dados

#### Estrutura no Railway

```
┌─────────────────────────────────────────────┐
│          Projeto "Matchpoint" no Railway    │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │   Serviço 1  │      │   Serviço 2     │ │
│  │              │      │                 │ │
│  │  PostgreSQL  │◄─────┤  Backend API    │ │
│  │   (Banco)    │      │    (FastAPI)    │ │
│  └──────────────┘      └─────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
         ▲
         │ String de conexão
         │ (credenciais seguras)
         │
    Frontend React
    (Vercel - grátis)
```

#### Acesso ao Banco de Dados

**1. Administrador (equipe dev):**

Pode acessar de várias formas:
- **Dashboard Web do Railway:** Interface visual no navegador
- **pgAdmin (desktop):** Ferramenta gráfica completa para PostgreSQL
- **DBeaver (desktop):** Interface mais amigável, suporta vários bancos
- **Linha de comando (psql):** Para operações avançadas

**String de conexão fornecida pelo Railway:**
```
postgresql://usuario:senha@containers-us-west-123.railway.app:5432/railway
```

**2. Sistema (backend FastAPI):**

Conecta automaticamente usando a mesma string:

```python
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL")  # Railway injeta automaticamente
engine = create_engine(DATABASE_URL)
```

**3. Múltiplos Acessos Simultâneos:**

- PostgreSQL gerencia conexões concorrentes automaticamente
- Railway permite 20-100 conexões simultâneas (suficiente para o MVP)
- Transações garantem que operações não conflitem
- Exemplo: dois caixas fechando comandas ao mesmo tempo = seguro

#### Segurança Automática

✅ O Railway já faz automaticamente:
- Criptografia SSL/TLS (dados trafegam seguros)
- Firewall (só apps autorizados conectam)
- Backups diários automáticos
- Senhas fortes geradas automaticamente

⚠️ Responsabilidade da equipe:
- Nunca commitar senhas no Git (usar variáveis de ambiente)
- Manter credenciais em arquivo `.env` local
- Revisar logs de acesso periodicamente

### 11.4 Alternativas Consideradas e Descartadas

| Provedor | Motivo da Exclusão |
|----------|-------------------|
| **Supabase** | Plano pago R$125/mês (estoura orçamento). Free tier pausa após 7 dias sem uso (risco operacional). Features avançadas desnecessárias no MVP. |
| **Render** | Custo maior ($7/mês vs $5/mês). Free tier pausa após 90 dias. Menos usado pela comunidade. |
| **VPS (Contabo/Hetzner)** | Requer configuração manual completa (Linux, PostgreSQL, Nginx). Maior complexidade de manutenção. Útil apenas para versão offline futura. |
| **Servidor próprio** | Sem backups automáticos. Dependente de energia/internet do bar. Impossibilita manutenção remota. |

### 11.5 Fluxo de Deploy

```
Desenvolvedor faz commit → Git push
         ↓
GitHub atualiza repositório
         ↓
    ┌────────────────────┐
    │                    │
    ▼                    ▼
Railway detecta     Vercel detecta
    ↓                    ↓
Build backend       Build frontend
    ↓                    ↓
Deploy automático   Deploy automático
    ↓                    ↓
API atualizada     Site atualizado
(5-10 segundos)    (20-30 segundos)
```

**Vantagem prática:** Ajustes semanais às terças podem ser deployados em menos de 1 minuto.

---

## 12. Cronograma de Desenvolvimento

| Data | Atividade | Responsável | Status |
|------|-----------|-------------|--------|
| 05/05 | Reunião de levantamento | Todos | ✅ Concluído |
| 05/05 → 11/05 | Cliente envia fotos do cardápio | Cliente | ⏳ Aguardando |
| 06/05 → 08/05 | Setup da infraestrutura (Railway + Vercel) | Dev | 🔄 Em andamento |
| 06/05 → 09/05 | Modelagem do banco + API base (Deep Models) | Backend Dev | 🔄 Em andamento |
| 07/05 → 10/05 | Telas principais do frontend | Frontend Dev | 🔄 Em andamento |
| 10/05 → 11/05 | Integração frontend + backend | Todos | ⏰ Planejado |
| 11/05 | Testes internos completos | QA | ⏰ Planejado |
| **12/05 — 16h00** | **Entrega do MVP no bar** | Equipe completa | 🎯 Deadline |
| 12/05 → 12/06 | Mês de teste gratuito | Ambos | — |
| Toda terça às 16h00 | Rodada semanal de ajustes | Ambos | — |
| 12/06 | Definição de plano + assinatura | Ambos | — |

---

## 13. Riscos e Mitigações

### 13.1 Riscos Técnicos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Queda de internet no bar | Alta | Alto | **MVP:** Risco aceito. **Roadmap:** Versão offline com sincronização |
| Queda de luz | Média | Alto | **MVP:** Risco aceito. **Roadmap:** Backup local |
| Sobrecarga em dia de jogo | Baixa | Médio | Railway escala automaticamente (pay-as-you-go) |
| Perda de dados | Muito Baixa | Crítico | Backups automáticos diários do Railway |
| Bug crítico em produção | Média | Alto | Hotfix via deploy em <5min. Rollback disponível |
| Concorrência no fechamento | Baixa | Alto | Transações ACID + last-write-wins no MVP |

### 13.2 Riscos de Negócio

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Cliente não se adaptar ao sistema | Baixa | Alto | Mês de teste gratuito. Ajustes semanais. UI extremamente simples |
| Garçons resistirem à mudança | Média | Médio | Período de transição com papel + digital. Treinamento simples |
| Cardápio não ser enviado a tempo | Baixa | Alto | Follow-up diário. Usar cardápio de exemplo se necessário |
| Prazo de 7 dias muito apertado | Média | Alto | Priorização rigorosa. Corte de escopo se necessário |

---

## 14. Critérios de Aceite do MVP

O MVP será considerado entregue quando atender **todos** os critérios abaixo.

### 14.1 Funcionalidades Core

- [ ] Sistema acessível via navegador no Dell do cliente
- [ ] Login único do estabelecimento (senha)
- [ ] Cadastro de pelo menos 20 itens do cardápio (incluindo compostos com ficha técnica)
- [ ] Cadastro de garçons, fornecedores, categorias, métodos de pagamento
- [ ] Abrir comanda nova (por nome ou mesa, com garçom obrigatório)
- [ ] Adicionar/editar/cancelar itens em comanda aberta (com cortesia, observação, pessoa associada)
- [ ] Aplicar desconto na comanda (% ou valor)
- [ ] Fechar comanda com cálculo automático
- [ ] Dividir conta (4 modalidades: sem divisão / igual / por pessoa / parcial)
- [ ] Pagamento misto (vários métodos numa mesma comanda)
- [ ] Geração de comprovante (não fiscal)
- [ ] Impressão via diálogo do navegador
- [ ] Reabertura de comanda fechada (com estorno de estoque)
- [ ] Registro de compras manuais (com cálculo de custo médio)
- [ ] Baixa automática de estoque ao fechar comanda (com explosão de compostos)
- [ ] Baixa sem venda (consumo interno/perda/cortesia)
- [ ] Histórico de movimentações de estoque
- [ ] Dashboard com indicadores e gráficos
- [ ] Relatórios: vendas do dia, fechamento de caixa, DRE, CMV por produto, vendas por garçom

### 14.2 Qualidade

- [ ] Zero bugs críticos (que impeçam uso básico)
- [ ] Tempo de resposta <2 segundos por operação
- [ ] Interface operável por "gente mais velha" (testado)
- [ ] Confirmação em todas as ações destrutivas
- [ ] Toasts de feedback consistentes
- [ ] Todos os fluxos documentados em manual simples

### 14.3 Entrega

- [ ] Sistema em produção (Railway + Vercel)
- [ ] Banco de dados populado com cardápio real
- [ ] Treinamento básico para 1 operador (15-30 minutos)
- [ ] Documentação de acesso (URLs, credenciais)
- [ ] Backup/exportação de dados disponível

---

## 15. Roadmap Pós-MVP

### 15.1 Mês de Teste (12/05 → 12/06)

Rodadas semanais de ajuste todas as terças às 16h00. Foco em:
- Correção de bugs encontrados no uso real
- Refinamento de UX (tamanhos de botão, mensagens, fluxos)
- Pequenas funcionalidades que aparecerem como críticas no uso

### 15.2 Pós-Contrato (visão de produto)

#### Curto prazo (primeiros meses)
- Atalhos de teclado no caixa
- Numeração sequencial de comandas (#001, #002...)
- Helper desktop para impressão direta na térmica
- Importação de XML de NFe + de-para de produtos
- Alertas no dashboard (estoque baixo, comanda antiga, produtos sem custo)
- Gestão de "comandas perdidas"
- Configuração direta da impressora Obitech WD-80R7

#### Médio prazo
- Multi-usuário com permissões (sócio, caixa, garçom)
- Comandas digitais com palm/tablet do garçom
- Versão offline com sincronização
- Cupom fiscal (NFCe) `[Confirmar com cliente]`
- Combos com regras de promoção
- Ficha técnica aninhada (insumo composto)
- Volume como unidade (ml/L)
- Custo de mão de obra/embalagem na ficha técnica
- Backup automático em nuvem

#### Longo prazo
- Delivery (iFood, próprio)
- Integração com motoboy
- Integração com maquininha PagBank
- Funcionalidades de IA (precificação inteligente, predição de demanda)
- App mobile dedicado
- Multi-loja

---

## 16. Contatos e Próximos Passos

### 16.1 Equipe do Projeto

| Papel | Nome | Contato |
|-------|------|---------|
| Product Owner | [A definir] | [A definir] |
| Tech Lead | [A definir] | [A definir] |
| Backend Dev | [A definir] | [A definir] |
| Frontend Dev | [A definir] | [A definir] |

### 16.2 Cliente

| Papel | Nome | Contato |
|-------|------|---------|
| Sócio 1 | [A definir] | [A definir] |
| Sócio 2 | [A definir] | [A definir] |
| Local | Estação Matchpoint | [Endereço] |

### 16.3 URLs do Projeto

| Ambiente | URL | Observação |
|----------|-----|------------|
| **Produção (Frontend)** | [A definir após deploy] | Vercel |
| **Produção (API)** | [A definir após deploy] | Railway |
| **Repositório** | [GitHub URL] | Privado |
| **Dashboard Railway** | railway.app | Backend + DB |
| **Dashboard Vercel** | vercel.com | Frontend |

### 16.4 Próximos Passos Imediatos

#### Até 07/05 (quinta)
1. ✅ Documentação completa unificada
2. 🔄 Setup Railway + Vercel (criar contas, configurar projetos)
3. 🔄 Criar repositório Git e estrutura inicial (Deep Models)
4. 🔄 Modelagem completa do banco de dados (incluindo Item, FichaTecnica, etc.)
5. ⏳ Aguardar fotos do cardápio do cliente

#### 08/05 - 10/05 (sex-dom)
1. Backend: APIs de itens, comandas, compras, estoque (seguindo Deep Models)
2. Frontend: Telas principais (Dashboard, Comandas, Lançamento, Fechamento)
3. Integração: Frontend consumindo API

#### 11/05 (seg)
1. Testes internos completos
2. Cadastro de itens do cardápio real
3. Ensaio de entrega e treinamento

#### 12/05 (ter) — 16h00
1. 🎯 **Entrega oficial no bar**
2. Treinamento da equipe (30min)
3. Primeira operação assistida

---

## 17. Anexos

### A. Glossário

| Termo | Significado |
|-------|-------------|
| **CMV** | Custo da Mercadoria Vendida (custo de compra dos produtos vendidos) |
| **Comanda** | Registro de consumo de um cliente ou mesa |
| **MVP** | Minimum Viable Product (Produto Mínimo Viável) |
| **Ficha técnica** | Receita de um item composto (insumos + quantidades) |
| **Item composto** | Item que se decompõe em insumos via ficha técnica (ex: X-Burguer) |
| **Item simples** | Item que é vendido/consumido como veio (ex: Coca Lata) |
| **Vendável** | Item que pode ser lançado em comanda (vs. insumo puro como carne moída) |
| **Baixa sem venda** | Saída de estoque que não gera receita (consumo interno, perda, quebra) |
| **Cortesia** | Item lançado em comanda com preço zero |
| **Custo médio ponderado** | Cálculo de custo do estoque considerando o histórico de compras |
| **Pagamento misto** | Comanda paga com mais de um método (ex: PIX + Crédito) |
| **DRE** | Demonstração do Resultado do Exercício |
| **Deploy** | Processo de colocar código em produção |
| **String de conexão** | URL com credenciais para acessar o banco de dados |
| **Deep Models** | Arquitetura em camadas separando Controllers, Services, Repositories e Models |
| **DTO** | Data Transfer Object — objeto para transferência de dados entre camadas |
| **Repository Pattern** | Padrão que isola acesso a dados da lógica de negócio |
| **Service Layer** | Camada que concentra toda a lógica de negócio |
| **ACID** | Atomicidade, Consistência, Isolamento, Durabilidade (propriedades de transações) |

### B. Referências Técnicas

- **FastAPI:** https://fastapi.tiangolo.com/
- **React:** https://react.dev/
- **TailwindCSS:** https://tailwindcss.com/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **Railway:** https://docs.railway.app/
- **Vercel:** https://vercel.com/docs
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Pydantic:** https://docs.pydantic.dev/
- **Repository Pattern:** https://martinfowler.com/eaaCatalog/repository.html
- **Service Layer:** https://martinfowler.com/eaaCatalog/serviceLayer.html

---

## Histórico de Versões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 (fluxo) | 05/05/2026 | Equipe dev | Documento inicial — fluxo completo do sistema |
| 1.0 (técnico) | 05/05/2026 | Equipe dev | Documento técnico — arquitetura e infraestrutura |
| 2.0 | 06/05/2026 | Equipe dev | Unificação dos documentos. Arquitetura Deep Models atualizada para refletir entidades ricas (Item composto/simples, FichaTecnica, Garçom, Pagamento misto, etc.) |
| **2.1** | **06/05/2026** | **Equipe dev** | **Adições pós-revisão de gaps: stack frontend completa (TanStack Query, Zustand, RHF+Zod, shadcn, sonner), estrutura de pastas FE, suporte mínimo 1280×720, padrões transversais (concorrência via `version`, timezone America/Sao_Paulo, padrão de erros, Alembic+seeds, structlog+Sentry, env vars, CORS, health, backup, auditoria de comanda), §9.5 com decisões de regra de negócio, ressalva sobre Railway/Vercel ainda não integrados. PRD criado em `docs/prd_matchpoint_mvp.md`.** |

---

**Documento criado em:** 05/05/2026
**Última atualização:** 06/05/2026
**Versão:** 2.1 (Unificada + Refinamento de Gaps)
**Status:** ✅ Aprovado para desenvolvimento
**Documentos relacionados:** `docs/prd_matchpoint_mvp.md`

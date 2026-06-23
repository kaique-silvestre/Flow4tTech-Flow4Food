# Flow4Food — Planejamento V2

> **Documento de arquitetura.** Escopo: melhorias planejadas para a V2, a serem iniciadas **somente após a V1 estar estável em produção.**
>
> O baseline e as pendências da V1 vivem em `v1-pendencias.md`. Este documento pressupõe que multi-tenancy, billing e auditoria de caixa da V1 já estão em produção.
>
> **Decisões de design registradas em 2026-06-09** — ver seção de decisões em cada módulo.

---

## Sumário

1. [Permissões V1.5 — Templates + Perfis Customizáveis](#1-permissões-v15)
2. [Painel do Administrador Global](#2-painel-do-administrador-global)
3. [Backlog V2+](#3-backlog-v2)
   - [3.X — Módulo de Calendário de Eventos](#3x-módulo-de-calendário-de-eventos)
   - [3.Y — Motor de Promoções e Recorrência](#3y-motor-de-promoções-e-recorrência)
   - [3.Z — Consolidação do Calendário: Contas a Pagar e Entregas](#3z-consolidação-do-calendário)
4. [Ordem de Execução Sugerida](#4-ordem-de-execução-sugerida)

---

## 1. Permissões V1.5

**Decisão:** NÃO implementar sistema de ações granulares (ALLOW/DENY por ação). Custo de migração, UI e manutenção supera o valor para o perfil atual de cliente (restaurante). Quando clientes enterprise com requisitos de compliance chegarem, migrar com base estabelecida.

**V1.5 mantém o modelo de telas** (`profile_permissions.screen`) e adiciona:
- Templates de perfil (conjuntos de telas pré-configurados)
- Perfis totalmente customizáveis por tenant
- `profile_id` nullable para "usuário livre"

### Modelagem de Banco de Dados

```sql
-- Templates de permissão (conjuntos de telas)
CREATE TABLE permission_templates (
    id          BIGSERIAL    PRIMARY KEY,
    nome        VARCHAR(60)  NOT NULL,
    descricao   VARCHAR(200),
    is_system   BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE TABLE template_permissions (
    template_id BIGINT      NOT NULL REFERENCES permission_templates(id) ON DELETE CASCADE,
    screen      VARCHAR(50) NOT NULL,
    can_access  BOOLEAN     NOT NULL DEFAULT TRUE,
    PRIMARY KEY (template_id, screen)
);

-- Perfil vincula ao template (opcional)
ALTER TABLE profiles ADD COLUMN template_id BIGINT REFERENCES permission_templates(id);
-- template_id NOT NULL => perfil travado no template; NULL => perfil custom editável

-- Usuário livre (sem perfil fixo)
ALTER TABLE system_users ALTER COLUMN profile_id DROP NOT NULL;
-- NULL profile_id => permissões lidas de user_permissions diretamente
CREATE TABLE user_permissions (
    id          BIGSERIAL   PRIMARY KEY,
    tenant_id   BIGINT      NOT NULL REFERENCES tenants(id),
    user_id     BIGINT      NOT NULL REFERENCES system_users(id) ON DELETE CASCADE,
    screen      VARCHAR(50) NOT NULL,
    can_access  BOOLEAN     NOT NULL DEFAULT TRUE,
    UNIQUE (user_id, screen)
);
```

### 1.1 Resolução de Permissão

Ordem de leitura ao montar o JWT:

1. `profile.template_id IS NOT NULL` → lê telas de `template_permissions` diretamente (nunca copia para `profile_permissions`)
2. `profile.template_id IS NULL` → lê de `profile_permissions` (custom)
3. `system_users.profile_id IS NULL` → lê de `user_permissions`

Ausência de registro = acesso negado.

### 1.2 Estratégia de JWT

- Access token: **15 minutos**
- Permissões embutidas no JWT como lista de telas: `permissions: ["comandas", "caixa", ...]`
- Ao fazer refresh, recomputa permissões do banco — mudança de perfil/template kick in em até 15min
- Sem overhead por request; sem leitura de banco em cada endpoint protegido

### 1.3 Templates Travam Edição Manual

Enquanto `profile.template_id IS NOT NULL`:
- `profile_permissions` ficam **bloqueadas** (checkboxes read-only na UI)
- Mudam apenas se o template for atualizado pela plataforma — propagação automática (próximo refresh do token)
- Para editar manualmente: desvincular template → `template_id = NULL` → perfil custom

### 1.4 Migração V1 → V1.5

- Perfis fixos existentes (Admin, Gerente, Caixa) viram **templates de sistema** (`is_system = TRUE`)
- Criar `template_permissions` correspondentes a cada `profile_permissions` atual
- `profile.template_id` populado para perfis que eram "hardcoded"
- `system_users.profile_id` permanece NOT NULL para usuários existentes — nullable apenas para novos "usuários livres"
- `require_permission(screen)` continua funcionando sem alteração

---

## 2. Painel do Administrador Global

Painel exclusivo dos **donos do SaaS** (não dos clientes): visão de todas as empresas, usuários de cada uma e gestão de assinaturas.

### Identidade da Plataforma (separada de `system_users`)

```sql
CREATE TABLE platform_admins (
    id              BIGSERIAL    PRIMARY KEY,
    email           VARCHAR(254) NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    password_hash   VARCHAR(200) NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

> JWT do platform admin: mesmo `JWT_SECRET`, claim `platform_admin: true`, sem `tenant_id`.

### 2.1 Auth e Roteamento

- Endpoint separado: `POST /api/platform/auth/login`
- Middleware: toda rota `/api/platform/*` exige `platform_admin: true` no JWT antes de qualquer lógica
- Engine de banco separado: `DATABASE_URL_PLATFORM` no settings — role PostgreSQL com `BYPASSRLS`, pool dedicado, nunca compartilhado com o app cliente

| Contexto | Role | Pool |
|----------|------|------|
| App dos clientes (`/api/*`) | `app_user` (RLS ativo) | Pool padrão |
| Painel admin (`/api/platform/*`) | Role com `BYPASSRLS` | Pool dedicado via `DATABASE_URL_PLATFORM` |

> **Atenção:** vazamento de auth em `/api/platform/*` expõe todos os tenants. Middleware de autenticação deve ser o primeiro handler — sem exceção.

### 2.2 Escopo do Painel V2 (sem KPIs)

Escopo de entrega inicial — **sem métricas**. KPIs serão especificados quando requisitos de negócio fecharem e entregues como §2.1 separado.

- Listar todas as empresas (tenants)
- Ver usuários por tenant
- Ativar / suspender assinatura (`UPDATE assinaturas SET status = ...`)

### 2.3 KPIs (futuro — §2.1)

Quando requisitos fecharem: tabela de cache/agregação assíncrona alimentada por job (snapshot periódico), evitando cálculos on-the-fly sobre tabelas grandes.

```sql
-- FUTURO — colunas a definir conforme KPIs reais
CREATE TABLE tenant_metrics_daily (
    tenant_id   BIGINT  REFERENCES tenants(id),
    dia         DATE,
    PRIMARY KEY (tenant_id, dia)
);
```

---

## 3. Backlog V2+

### 3.X — Módulo de Calendário de Eventos

**Escopo:** Tenants agendam e visualizam dias de eventos (casamentos, aniversários, shows, festivais) via aba de Calendário Visual.

#### Banco de Dados

```sql
CREATE TABLE tenant_eventos (
    id          BIGSERIAL    PRIMARY KEY,
    tenant_id   BIGINT       NOT NULL REFERENCES tenants(id),
    titulo      VARCHAR(100) NOT NULL,
    descricao   TEXT,
    data_evento DATE         NOT NULL,
    criado_por  BIGINT       NOT NULL REFERENCES system_users(id),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenant_eventos_data ON tenant_eventos(tenant_id, data_evento);
```

> `data_evento` é DATE sem timezone — armazenado no horário local do tenant (capturado server-side via config do estabelecimento).

#### UX — Dois Fluxos de Criação

| Fluxo | Comportamento |
|-------|---------------|
| **Botão `+`** | Modal com Título, Descrição e Data (campo vazio, usuário escolhe) |
| **Clique na Data** | Mesmo modal com Data **pré-preenchida e travada** |

Ambos mapeiam para o mesmo endpoint de criação.

#### Permissões (V1.5 — telas)

Adicionar tela `"calendario"` ao catálogo de telas existente. Templates Admin e Gerente recebem acesso; Caixa não.

---

### 3.Y — Motor de Promoções e Recorrência

**Escopo:** Itens do cardápio em promoção com janelas de horas/dias e recorrência (semanal ou mensal), com integração visual ao Calendário (§3.X).

#### Banco de Dados

```sql
CREATE TYPE tipo_recorrencia AS ENUM ('nenhuma', 'semanal', 'mensal');

CREATE TABLE promocoes (
    id              BIGSERIAL        PRIMARY KEY,
    tenant_id       BIGINT           NOT NULL REFERENCES tenants(id),
    nome            VARCHAR(100)     NOT NULL,
    descricao       TEXT,
    tipo_desconto   VARCHAR(10)      NOT NULL CHECK (tipo_desconto IN ('porcentagem', 'valor_fixo')),
    valor_desconto  NUMERIC(10,2)    NOT NULL,

    data_inicio     DATE             NOT NULL,
    data_fim        DATE,                               -- NULL = por tempo indeterminado
    hora_inicio     TIME             NOT NULL DEFAULT '00:00:00',
    hora_fim        TIME             NOT NULL DEFAULT '23:59:59',

    recorrencia     tipo_recorrencia NOT NULL DEFAULT 'nenhuma',
    dias_semana     INT[]            NULL,               -- 0=Dom..6=Sáb; só quando recorrencia='semanal'
    dias_mes        INT[]            NULL,               -- 1..31; só quando recorrencia='mensal'

    criado_por      BIGINT           NOT NULL REFERENCES system_users(id),
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

CREATE TABLE promocao_produtos (
    promocao_id     BIGINT  NOT NULL REFERENCES promocoes(id) ON DELETE CASCADE,
    produto_id      BIGINT  NOT NULL,
    PRIMARY KEY (promocao_id, produto_id)
);

CREATE INDEX idx_promocoes_vigencia ON promocoes(tenant_id, data_inicio, data_fim);
```

#### Validação de `dias_semana` / `dias_mes`

Pydantic validator no schema (não no banco):

- `recorrencia = 'nenhuma'` → forçar `dias_semana = None`, `dias_mes = None`
- `recorrencia = 'semanal'` → exigir `dias_semana` não-vazio
- `recorrencia = 'mensal'` → exigir `dias_mes` não-vazio

#### Conflito de Promoções

Se dois promos ativos cobrem o mesmo produto no mesmo horário: aplica o de **menor `id`** (mais antigo). Documentado na UI: *"Produto em múltiplas promoções ativas: aplica a mais antiga."*

#### Engine de Desconto no PDV

```
SE (DataAtual ENTRE data_inicio E data_fim OU data_fim IS NULL)
E  (HoraAtual ENTRE hora_inicio E hora_fim)
E  (SE recorrencia == 'semanal' → DiaDaSemanaAtual ∈ dias_semana)
E  (SE recorrencia == 'mensal'  → DiaDoMesAtual ∈ dias_mes)
ENTÃO aplica desconto sobre valor original do produto
     (ORDER BY id ASC LIMIT 1 se múltiplas promos)
```

#### Integração Visual com o Calendário

- Eventos (§3.X) em azul, Promoções em verde
- Expansão de recorrência calculada no front-end ao renderizar o mês
- Popover de detalhe: vigência + dias + itens inclusos

---

### 3.Z — Consolidação do Calendário

**Escopo:** Calendário Visual como cockpit de gestão — camadas: Eventos, Promoções, Contas a Pagar, Entregas.

#### Decisão de Design: View SQL corrigida

O esboço original da view referenciava tabelas e colunas inexistentes no codebase. Nomes corrigidos:

| Esboço original (errado) | Real no codebase |
|---|---|
| `financeiro_contas_pagar` | `contas_pagar` |
| `fornecedor_nome` (string) | `fornecedor_id` FK → JOIN em `fornecedores` |
| `compras_pedidos` | `compras` |
| `status = 'aguardando_entrega'` | `status = 'confirmado'` (pedido feito, não recebido) |
| `data_entrega_prevista` | `data_prevista_recebimento` |
| `hora_entrega_prevista` | não existe — usar `'08:00:00'` como placeholder |
| Promoções ausentes do UNION ALL | adicionar camada verde |

#### View Corrigida

```sql
CREATE OR REPLACE VIEW view_calendario_consolidado AS

-- Camada 1: Eventos
SELECT e.tenant_id, e.data_evento AS data_referencia, 'evento' AS tipo,
       e.id AS referencia_id, e.titulo AS descricao, '00:00:00'::TIME AS hora_inicio
FROM tenant_eventos e

UNION ALL

-- Camada 2: Promoções (calculadas no front; esta camada serve como marcador de vigência)
SELECT p.tenant_id, p.data_inicio AS data_referencia, 'promocao' AS tipo,
       p.id AS referencia_id, p.nome AS descricao, p.hora_inicio
FROM promocoes p
WHERE p.data_fim IS NULL OR p.data_fim >= CURRENT_DATE

UNION ALL

-- Camada 3: Contas a Pagar
SELECT cp.tenant_id, cp.data_vencimento AS data_referencia, 'conta_pagar' AS tipo,
       cp.id AS referencia_id,
       'Vencimento: ' || COALESCE(f.nome, 'Fornecedor não informado') AS descricao,
       '08:00:00'::TIME AS hora_inicio
FROM contas_pagar cp
LEFT JOIN fornecedores f ON f.id = cp.fornecedor_id
WHERE cp.status = 'pendente'

UNION ALL

-- Camada 4: Entregas de Fornecedores (compras confirmadas não recebidas)
SELECT c.tenant_id, c.data_prevista_recebimento AS data_referencia, 'entrega_insumo' AS tipo,
       c.id AS referencia_id,
       'Entrega: ' || COALESCE(f.nome, 'Fornecedor não informado') AS descricao,
       '08:00:00'::TIME AS hora_inicio
FROM compras c
LEFT JOIN fornecedores f ON f.id = c.fornecedor_id
WHERE c.status = 'confirmado'
  AND c.data_prevista_recebimento IS NOT NULL;
```

#### UI/UX — Sistema de Camadas

| Cor | Camada |
|-----|--------|
| Azul | Eventos de Clientes |
| Verde | Promoções Ativas |
| Vermelho | Contas a Pagar |
| Amarelo | Entregas de Fornecedores |

Toggles de filtro: checkboxes para ligar/desligar cada camada individualmente.

**Deep Linking:**

| Card | Comportamento |
|------|---------------|
| Conta a Pagar | Modal com valor + código de barras + botão *"Ir para o Financeiro"* |
| Entrega | Painel com insumos esperados + botão *"Dar Entrada no Estoque"* |

#### Segurança (permissões de tela)

| Dado no calendário | Tela necessária |
|--------------------|----------------|
| Contas a Pagar | `"calendario"` **E** `"financeiro"` |
| Entregas | `"calendario"` **E** `"estoque"` |

Dados ausentes da tela se usuário não tiver a tela correspondente — omitidos em nível de API.

---

## 4. Ordem de Execução Sugerida

> **Pré-requisito:** V1 (multi-tenancy + billing + auditoria de caixa) em produção e estável.

| Prioridade | Módulo | Dependência |
|------------|--------|-------------|
| 1 | **Permissões V1.5 — Templates + Perfis Customizáveis** (§1) | V1 estável |
| 2 | **Painel Admin Global** (§2, sem KPIs) | V1 + multi-tenancy + billing |
| 2.1 | **KPIs do Painel Admin** | §2 + definição de requisitos de negócio |
| 3 | **Calendário de Eventos** (§3.X) | V1 estável |
| 4 | **Motor de Promoções** (§3.Y) | Calendário §3.X |
| 5 | **Cockpit Consolidado** (§3.Z) | §3.X + §3.Y + módulos Financeiro e Estoque V1 |
| — | **Backlog incremental restante** | Conforme demanda de mercado |

---

### Backlog Restante (sem data definida)

- **Permissões granulares por ação (ALLOW/DENY):** reavaliar quando clientes enterprise com requisitos de compliance ou auditoria chegarem. Base V1.5 permite migração incremental.
- **Módulo de Planos e Precificação:** modelo comercial não definido. Quando fechar: catálogo de planos, limites/quotas, vínculo com `assinaturas`, fluxo de troca de plano no painel admin.
- **Sub-receita (insumo composto):** ficha técnica recursiva.
- **Histórico de auditoria visual:** navegar `eventos_comanda` com filtros.
- **Relatórios avançados de CMV / margem por prato.**
- **Roteamento de impressão por setor, KDS, cardápio QR Code, módulo fiscal (NFC-e / SAT).**

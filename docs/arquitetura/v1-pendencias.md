# V1 — Pendências para Lançamento Comercial (Flow4Food)

> Documento de arquitetura. Stack: Python (FastAPI/SQLAlchemy) + PostgreSQL único + React, hospedado no Railway.
> Restrição estrutural: **um único banco de dados** para autenticação, tenants, billing e dados de negócio.
> Escopo: **somente o que falta implementar para a V1.** Melhorias da V2 vivem em [`v2-melhorias.md`](./v2-melhorias.md).

---

## 1. Arquivamento das Descobertas Atuais (Status do Protótipo)

Diagnóstico levantado a partir de leitura do código-fonte (não suposição). Serve de baseline para saber o que já existe e o que falta.

### 1.1 Optimistic Lock por versão — ✅ Funciona

A concorrência "vários garçons na mesma comanda" já está protegida por optimistic locking via coluna `version`.

- Implementação em `backend/src/repositories/comandas_repository.py:73` (`increment_version`).
- É um *compare-and-swap* atômico no banco:

```sql
UPDATE comandas SET version = version + 1, updated_at = :now
WHERE id = :id AND version = :version;
```

- `rowcount == 0` ⇒ versão divergente ⇒ o serviço devolve `409 COMANDA_DESATUALIZADA` e o cliente recarrega.
- **Manter como está.** É a abordagem correta para edição colaborativa de comanda.

> ⚠️ **Dívida conhecida (corrigir na V1):** `aplicar_desconto` e `cancelar_comanda` escrevem **sem** passar por `increment_version` (lost update silencioso). Padronizar: nenhuma mutação de comanda sem CAS de versão.

### 1.2 Race Condition na reserva de estoque — ⚠️ Corrigir (V1)

O fluxo de **compras/ajuste** já usa lock de linha (`estoque_repository.get_insumo_for_update`), mas o fluxo da **comanda não usa**.

- `backend/src/services/comandas_service.py:452-467` (`_reservar_estoque`) e `:514-526` (`_baixar_insumo`) fazem read-modify-write sobre `insumo.estoque_reservado` / `estoque_atual` após um `SELECT` simples.
- Dois lançamentos simultâneos do mesmo insumo leem o mesmo valor ⇒ **lost update** (uma reserva some).

**Correção:** migrar o fluxo da comanda para `SELECT ... FOR UPDATE`, reutilizando o repositório já existente.

```python
def _reservar_estoque(db, produto_id, quantidade):
    for comp in componentes:
        insumo = estoque_repository.get_insumo_for_update(db, comp.insumo_id)  # lock de linha
        insumo.estoque_reservado += comp.quantidade * quantidade
```

### 1.3 Produtos compostos & Auditoria — ✅ Existem

- **Ficha técnica / insumos / componentes:** implementados (`ficha_tecnica`, `insumos`). Reserva, baixa e estorno de insumo a partir do produto vendido já funcionam. Gap remanescente (V2): sub-receita (insumo composto de outro insumo) — ver `v2-melhorias.md`.
- **Eventos de auditoria:** tabela `eventos_comanda` registra `COMANDA_ABERTA`, `ITEM_LANCADO`, `ITEM_CANCELADO`, etc. Gap V1: `garcom_id`/`user_id` é opcional e fica nulo em vários eventos — tornar obrigatório para rastreabilidade.

### 1.4 Estado de Multi-tenancy — ❌ Inexistente (bloqueador V1)

- `estabelecimento` é uma **linha única (singleton)**, sem `tenant_id`.
- Tabelas operacionais (`comandas`, `itens_comanda`, `insumos`, `produtos`, `movimentos_estoque`, `compras`, `pagamentos`, `comissoes_garcom`) **não têm `tenant_id`**.
- Apenas `profiles.tenant_id` existe (vestigial, `server_default = 1`).
- **Conclusão:** sistema é hoje single-tenant. Esta é a evolução estrutural central da V1.

### 1.5 Permissões — ⚠️ Por tela + perfis fixos hardcoded

O RBAC atual é **por tela**, não por ação. Diagnóstico do código:

- Universo de permissões = lista fixa de telas em `backend/alembic/versions/0035_seed_default_profiles.py:20`:
  `dashboard, comandas, compras, estoque, cadastros, relatorios, configuracoes, gestao_usuarios`.
- Perfis padrão **hardcoded** na própria migration: `Admin`, `Gerente`, `Caixa` (`is_system = true`).
- `profile_permissions` guarda só linhas com `can_access = true` — **não existe DENY explícito**; ausência da linha = sem acesso.
- Enforcement: `require_permission(screen)` (`backend/src/api/dependencies.py:35`) checa se a tela está na lista `permissions` do JWT.
- Lógica acoplada a nomes: `profiles_service.py` bloqueia edição/desativação por `profile.name == "Admin"` (string mágica).
- `TENANT_ID = 1` está cravado em `users_service.py`, `profiles_service.py`, `auth_service.py` — precisa virar dinâmico (vem do JWT) na migração multi-tenant.

**Decisão de escopo:**
- **V1:** manter o modelo por tela. Os perfis fixos (Admin/Gerente/Caixa) **não** evoluem para um catálogo dinâmico de ações nesta versão — apenas seguem como estão, agora vinculados por `tenant_id`.
- **V2:** evoluir para permissões por **ação** com ALLOW/DENY e templates (ver `v2-melhorias.md`).

---

## 2. Especificação do Sistema de Empresas (Multi-tenancy)

### 2.1 Estratégia de isolamento

`tenant_id` como discriminador em todas as tabelas operacionais **+ PostgreSQL Row-Level Security (RLS)**. RLS torna o isolamento uma garantia do kernel do banco, não da disciplina do desenvolvedor: um `SELECT` sem `WHERE` correto não vaza dados de outro tenant. Custo de infra: zero (nativo no PostgreSQL do Railway).

### 2.2 Tabela `tenants` (substitui o singleton `estabelecimento`)

```sql
CREATE TABLE tenants (
    id              BIGSERIAL    PRIMARY KEY,
    razao_social    VARCHAR(200) NOT NULL,
    nome_fantasia   VARCHAR(200),
    cnpj            VARCHAR(14)  UNIQUE,                 -- somente dígitos; validar na app
    admin_user_id   BIGINT,                             -- FK setada após criar o usuário dono (ver 2.4)
    email_contato   VARCHAR(255) NOT NULL,
    telefone        VARCHAR(30),
    status          VARCHAR(20)  NOT NULL DEFAULT 'ativo'
                    CHECK (status IN ('ativo','suspenso','cancelado','trial')),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_tenants_cnpj ON tenants (cnpj) WHERE cnpj IS NOT NULL;
```

> `status` aqui é o estado **administrativo** da empresa (ativa, cancelada). O estado **financeiro** (assinatura em dia/vencida) vive em `assinaturas` (seção 3) — separação de responsabilidades.

### 2.3 `tenant_id` + RLS nas tabelas operacionais

> **Banco comercial começa limpo.** Os dados atuais do protótipo são apenas testes e **não** serão migrados. Logo, **não há `DEFAULT 1` provisório nem backfill** — a coluna `tenant_id` nasce `NOT NULL` sem default em cada tabela, populada exclusivamente pelo fluxo de onboarding (§2.4).

```sql
-- tenant_id NOT NULL (sem default) em TODAS as tabelas operacionais
ALTER TABLE comandas      ADD COLUMN tenant_id BIGINT NOT NULL REFERENCES tenants(id);
ALTER TABLE itens_comanda ADD COLUMN tenant_id BIGINT NOT NULL REFERENCES tenants(id);
ALTER TABLE insumos       ADD COLUMN tenant_id BIGINT NOT NULL REFERENCES tenants(id);
ALTER TABLE produtos      ADD COLUMN tenant_id BIGINT NOT NULL REFERENCES tenants(id);
-- ... movimentos_estoque, compras, pagamentos, comissoes_garcom, eventos_comanda, categorias, fornecedores

-- Índice composto: tenant_id SEMPRE como primeira coluna
CREATE INDEX idx_comandas_tenant_status ON comandas (tenant_id, status);

-- Row-Level Security
ALTER TABLE comandas ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON comandas
    USING (tenant_id = current_setting('app.tenant_id')::BIGINT);
```

**Injeção do tenant na sessão** (lido do JWT assinado, nunca de header/body):

```python
def get_db(payload: dict = Depends(get_current_user)) -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        db.execute(text("SET app.tenant_id = :tid"), {"tid": payload["tenant_id"]})
        yield db
    finally:
        db.close()
```

> 🔒 **Crítico:** RLS é ignorado por roles com `BYPASSRLS` (ex: superusuário/dono do banco). A aplicação **deve** conectar com um role PostgreSQL comum, sem esse privilégio. Caso contrário o isolamento é nulo.

### 2.4 Virada de chave no cadastro: usuário sempre vinculado a um tenant

Hoje o cadastro cria usuário sem vínculo de empresa. Regras novas da V1:

- **Todo usuário pertence a exatamente um tenant** (`system_users.tenant_id NOT NULL`).
- **E-mail é único globalmente quando informado** — constraint `UNIQUE` em `system_users.email` (coluna permanece **nullable**). Em Postgres, `UNIQUE` permite múltiplos `NULL`, então funcionários sem e-mail convivem; e-mails informados não podem repetir em todo o sistema. Decisão de produto: e-mail simplifica o login (identifica o usuário sem resolver tenant antes).
- **E-mail obrigatório apenas para Admin (dono da conta), opcional para os demais.** Regra de **aplicação**, não de schema: garçom/caixa/gerente podem ser criados só com username (realista — funcionário de bar raramente tem e-mail). Todo usuário com perfil **Admin** exige e-mail, pois é o contato que recebe cobrança (billing/`402`, §3.3) e recuperação de senha.
- **Todo usuário é criado obrigatoriamente associado a um perfil padrão** (Admin, Gerente ou Caixa) — `profile_id NOT NULL`.

```sql
ALTER TABLE system_users ADD COLUMN tenant_id BIGINT NOT NULL REFERENCES tenants(id);
-- E-mail único global quando preenchido; coluna segue nullable (funcionários sem e-mail)
ALTER TABLE system_users ADD CONSTRAINT uq_system_users_email UNIQUE (email);
```

> Validação do e-mail obrigatório do Admin vive no `users_service` (na criação/edição), não numa constraint do banco — o schema não distingue perfil. Ao criar usuário com perfil Admin sem e-mail ⇒ erro de validação.

**Perfis também são tenant-scoped + RLS.** `profiles` e `profile_permissions` recebem `tenant_id` e proteção RLS, exatamente como as tabelas operacionais (§2.3). Conceitualmente: um **perfil** é um conjunto de permissões de **visualização de telas** (modelo por tela da V1 — §1.5), e cada tenant tem sua própria cópia dos perfis padrão.

```sql
ALTER TABLE profiles            ADD COLUMN tenant_id BIGINT NOT NULL REFERENCES tenants(id);
ALTER TABLE profile_permissions ADD COLUMN tenant_id BIGINT NOT NULL REFERENCES tenants(id);

ALTER TABLE profiles            ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_permissions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON profiles
    USING (tenant_id = current_setting('app.tenant_id')::BIGINT);
CREATE POLICY tenant_isolation ON profile_permissions
    USING (tenant_id = current_setting('app.tenant_id')::BIGINT);
```

> `profiles.tenant_id` hoje é vestigial (`server_default = 1`, §1.5) — na V1 passa a ser carregado de verdade e isolado por RLS.

Dois fluxos de criação de usuário:

**(a) Onboarding (empresa nova) — transação única:**

```
1. BEGIN
2. INSERT tenants            -> tenant_id
3. CLONAR perfis padrão para o novo tenant_id:
   - copiar profiles (Admin, Gerente, Caixa) com o novo tenant_id  -> {admin_profile_id, ...}
   - copiar profile_permissions (telas de cada perfil) com o novo tenant_id
   (cada tenant nasce com sua própria cópia isolada dos perfis e permissões de tela)
4. INSERT system_users (dono, tenant_id, profile_id = admin_profile_id)  -> user_id
5. UPDATE tenants SET admin_user_id = user_id WHERE id = tenant_id
6. INSERT assinaturas (tenant_id, plano = 'trial', ...)   -- ver seção 3
7. COMMIT
```

O tenant, seus perfis padrão e o primeiro admin nascem juntos e atomicamente. Falha em qualquer passo ⇒ rollback total (não fica empresa órfã sem dono, nem usuário sem perfil). O clone dos perfis (passo 3) usa o seed atual (`0035_seed_default_profiles.py`) como molde — as mesmas telas por perfil, agora carimbadas com o `tenant_id` novo.

**(b) Funcionário (garçom, gerente):** criado **dentro** de um tenant existente, por um admin daquele tenant. O `tenant_id` vem do JWT do admin logado — **nunca** do payload do formulário (senão um admin criaria usuário em outra empresa).

```python
def criar_funcionario(db, admin_payload: dict, dados: NovoUsuario):
    novo = SystemUser(
        tenant_id=admin_payload["tenant_id"],   # herdado do admin, não do request
        email=dados.email,
        profile_id=dados.profile_id,
    )
```

**Claims obrigatórios no JWT** após esta mudança:

```json
{
  "user_id": 42,
  "tenant_id": 7,
  "permissions": ["comandas", "estoque"],
  "subscription_status": "ativo",
  "exp": 1717000000
}
```

---

## 3. Sistema de Assinaturas e Bloqueio (Billing Control)

### 3.1 Modelagem

Três tabelas: catálogo de planos, assinatura por tenant e histórico de pagamentos (auditoria financeira).

```sql
-- Catálogo de planos (poucos registros, editável pelo admin da plataforma)
CREATE TABLE planos (
    id              BIGSERIAL    PRIMARY KEY,
    nome            VARCHAR(50)  NOT NULL,              -- 'Básico', 'Pro'
    preco_mensal    NUMERIC(10,2) NOT NULL,
    max_usuarios    INT,                                -- NULL = ilimitado
    max_comandas_mes INT,                               -- limites de uso por plano
    ativo           BOOLEAN      NOT NULL DEFAULT TRUE
);

-- Uma assinatura corrente por tenant
CREATE TABLE assinaturas (
    id                BIGSERIAL   PRIMARY KEY,
    tenant_id         BIGINT      NOT NULL UNIQUE REFERENCES tenants(id),
    plano_id          BIGINT      NOT NULL REFERENCES planos(id),
    status            VARCHAR(20) NOT NULL DEFAULT 'trial'
                      CHECK (status IN ('trial','ativa','vencida','cancelada','suspensa')),
    inicio            DATE        NOT NULL DEFAULT CURRENT_DATE,
    data_vencimento   DATE        NOT NULL,             -- próxima cobrança / fim do ciclo
    cancelada_em      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_assinaturas_vencimento ON assinaturas (status, data_vencimento);

-- Histórico de pagamentos (append-only; base de conciliação)
CREATE TABLE pagamentos_assinatura (
    id              BIGSERIAL    PRIMARY KEY,
    assinatura_id   BIGINT       NOT NULL REFERENCES assinaturas(id),
    valor           NUMERIC(10,2) NOT NULL,
    pago_em         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    periodo_inicio  DATE         NOT NULL,
    periodo_fim     DATE         NOT NULL,
    gateway_ref     VARCHAR(100),                       -- id da transação no provedor
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

### 3.2 Máquina de estados da assinatura

```
trial ──(pagamento)──► ativa
trial ──(prazo expira sem pagar)──► vencida
ativa ──(data_vencimento passa sem pagamento)──► vencida
vencida ──(pagamento)──► ativa
ativa/vencida ──(cliente cancela)──► cancelada
qualquer ──(decisão admin plataforma)──► suspensa
```

- `ativa` e `trial` ⇒ **acesso liberado**.
- `vencida`, `cancelada`, `suspensa` ⇒ **acesso bloqueado** (apenas login + tela de pagamento).

### 3.3 Lógica de ativação/desativação de acesso

Combinação de **JWT (rápido, sem I/O)** + **verificação no banco (autoritativa)**. O ponto-chave: bloquear/liberar uma empresa inteira **não pode** exigir varrer e editar cada funcionário.

**Camada 1 — JWT carrega o estado (otimista, baixo custo):**
O claim `subscription_status` é gravado no login. Middleware barra requests de negócio se ≠ `ativo`/`trial`. Como o JWT é curto (access token em memória, refresh httpOnly — já implementado no projeto), o estado se auto-corrige a cada renovação. Sem polling no banco a cada request.

**Camada 2 — Banco é a fonte da verdade (na renovação do token):**
No **refresh** do token, reler `assinaturas.status` do tenant e reemitir o access token com o `subscription_status` atual. Assim, suspender uma empresa propaga para **todos** os funcionários no próximo refresh (minutos), sem tocar em nenhuma linha de usuário.

```python
def require_active_subscription(payload: dict = Depends(get_current_user)) -> dict:
    if payload.get("subscription_status") not in ("ativo", "trial"):
        raise HTTPException(status_code=402, detail="Assinatura inativa")  # 402 Payment Required
    return payload
```

**Comportamento do Frontend (React) ao receber 402.** O interceptor HTTP trata o `402` de forma diferenciada conforme o perfil do usuário logado:

- **Admin (dono):** redirecionar para uma tela amigável de **bloqueio financeiro** — explica que a assinatura está vencida/suspensa, com instruções de pagamento e contato com o suporte da **Flow4Tech**. É a pessoa que pode resolver, então recebe o caminho de regularização.
- **Demais perfis (Gerente, Caixa, Garçom):** exibir apenas uma mensagem direta — "A conta da empresa está temporariamente suspensa. Procure o responsável." — bloqueando o acesso às telas operacionais. Não recebem dados de pagamento (não é responsabilidade deles).

> Ambos partem do mesmo `402` do backend; a diferença é só de UI, decidida pelo `profile_name`/`permissions` do JWT no cliente. O backend não muda de comportamento por perfil.

**Bloqueio imediato (sem esperar expirar o access token):** o tenant suspenso entra numa checagem barata. Como `subscription_status` também é validado na renovação e o access token é curto, a janela de exposição é o TTL do access token (configurar ≤ 15 min). Para corte imediato em caso crítico, revogar os refresh tokens do tenant (a infra de `revoked_tokens` já existe no projeto).

**Desativar empresa inteira = 1 UPDATE:**

```sql
-- Suspender empresa (cobrança falhou / cancelamento) — operação O(1)
UPDATE assinaturas SET status = 'suspensa', updated_at = NOW() WHERE tenant_id = :tid;
-- Reativar após pagamento
UPDATE assinaturas SET status = 'ativa', data_vencimento = :nova_data WHERE tenant_id = :tid;
```

Nenhuma alteração em `system_users`. O vínculo `usuário → tenant → assinatura` faz o bloqueio fluir por toda a empresa a partir de uma única linha.

**Job de vencimento (scheduler já existe no projeto — `core/scheduler.py`):**

```sql
-- Diário: marca como vencidas as assinaturas cujo ciclo passou
UPDATE assinaturas
SET status = 'vencida', updated_at = NOW()
WHERE status IN ('ativa','trial') AND data_vencimento < CURRENT_DATE;
```

### 3.4 Resumo do fluxo de decisão de acesso

```
Request de negócio
   │
   ├─ JWT válido? ───────────────── não ─► 401
   │       │ sim
   ├─ subscription_status ∈ {ativo,trial}? ─ não ─► 402 (tela de pagamento)
   │       │ sim
   ├─ tem permissão da ação? ────── não ─► 403
   │       │ sim
   └─ SET app.tenant_id ─► query isolada por RLS ─► 200
```

---

## 4. Auditoria de Caixa

Não existe no sistema hoje. É requisito V1: o dono precisa abrir/fechar o caixa do dia e conciliar o dinheiro físico contra o que o sistema registrou. Modelo separado da auditoria de comanda (`eventos_comanda`), que continua sendo o registro bruto operacional.

### 4.1 Modelagem

Duas tabelas: a sessão de caixa (turno entre abertura e fechamento) e os movimentos manuais de dinheiro (sangria, suprimento).

```sql
-- Sessão de caixa: um turno aberto por operador
CREATE TABLE caixa_sessoes (
    id                  BIGSERIAL    PRIMARY KEY,
    tenant_id           BIGINT       NOT NULL REFERENCES tenants(id),
    aberto_por          BIGINT       NOT NULL REFERENCES system_users(id),
    fechado_por         BIGINT       REFERENCES system_users(id),
    status              VARCHAR(20)  NOT NULL DEFAULT 'aberto'
                        CHECK (status IN ('aberto','fechado')),
    valor_abertura      NUMERIC(10,2) NOT NULL DEFAULT 0,   -- fundo de troco inicial
    valor_fechamento_informado NUMERIC(10,2),               -- dinheiro contado na gaveta
    valor_fechamento_calculado NUMERIC(10,2),               -- o que o sistema esperava
    diferenca           NUMERIC(10,2),                       -- informado - calculado (quebra/sobra)
    aberto_em           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    fechado_em          TIMESTAMPTZ,
    observacao          VARCHAR(500)
);

-- Apenas uma sessão aberta por tenant ao mesmo tempo
CREATE UNIQUE INDEX uq_caixa_aberto_por_tenant
    ON caixa_sessoes (tenant_id) WHERE status = 'aberto';

-- Movimentos manuais de dinheiro dentro de uma sessão (append-only)
CREATE TABLE caixa_movimentos (
    id              BIGSERIAL    PRIMARY KEY,
    tenant_id       BIGINT       NOT NULL REFERENCES tenants(id),
    sessao_id       BIGINT       NOT NULL REFERENCES caixa_sessoes(id),
    tipo            VARCHAR(20)  NOT NULL
                    CHECK (tipo IN ('sangria','suprimento')),   -- retirada / aporte
    valor           NUMERIC(10,2) NOT NULL CHECK (valor > 0),
    motivo          VARCHAR(300),
    registrado_por  BIGINT       NOT NULL REFERENCES system_users(id),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_caixa_mov_sessao ON caixa_movimentos (tenant_id, sessao_id);
```

> RLS por `tenant_id` aplicada às duas tabelas, igual às operacionais (§2.3).

### 4.2 Fluxo lógico

```
Abertura:  INSERT caixa_sessoes (status='aberto', valor_abertura = fundo de troco)
           — falha se já existe sessão aberta (índice único parcial)

Durante:   sangria/suprimento -> INSERT caixa_movimentos
           vendas em dinheiro já vivem em `pagamentos` (metodo.tipo='dinheiro')

Fechamento:
  valor_calculado = valor_abertura
                  + SUM(pagamentos em dinheiro no período da sessão)
                  + SUM(suprimentos) - SUM(sangrias)
  diferenca = valor_fechamento_informado - valor_calculado
  UPDATE caixa_sessoes SET status='fechado', fechado_em=NOW(),
         valor_fechamento_calculado, valor_fechamento_informado, diferenca
```

`diferenca < 0` = quebra (falta dinheiro); `> 0` = sobra. O valor calculado deriva de `pagamentos` filtrados pela janela `aberto_em..fechado_em` da sessão — não duplica dados de venda, apenas concilia.

**Permissão:** abertura/fechamento de caixa ficam atrás de `require_permission("caixa")` (nova tela no universo V1) ou da tela `comandas`, conforme decisão de produto.

---

## 5. Rebranding: Matchpoint → Flow4Food (produto da Flow4Tech)

Decisão de produto: aposentar o nome interno "Matchpoint". O sistema passa a se chamar **Flow4Food** (exibido como "Flow for Food"), posicionado como **produto da empresa Flow4Tech**.

**Relação de marca a comunicar na UI:**
- **Flow4Tech** = empresa (a casa).
- **Flow4Food** = produto de gestão de comandas dessa empresa.
- Sugestão de assinatura visual no card de login / rodapé: logo/nome "Flow4Food" em destaque + linha menor "por Flow4Tech" (ou "um produto Flow4Tech").

**Pontos de toque a alterar (mapeados no código):**

| Local | Arquivo | Hoje |
|---|---|---|
| Título da aba | `frontend/index.html:6` | `<title>Matchpoint</title>` |
| Card de login | `frontend/src/features/auth/LoginPage.tsx` | "Flow4Tech" |
| Topbar | `frontend/src/components/layout/Topbar.tsx` | marca atual |
| Telas de senha | `frontend/src/features/auth/{RedefinirSenhaPage,EsqueciSenhaPage}.tsx` | marca atual |
| Placeholder | `frontend/src/pages/PlaceholderPage.tsx` | marca atual |
| Título da API | `backend/src/main.py:48` | `title="Matchpoint API"` |
| Assunto do e-mail | `backend/src/services/auth_service.py:163` | "— Flow4Tech" |

> A separação empresa/produto (Flow4Tech ⊃ Flow4Food) casa com o modelo multi-tenant: a Flow4Tech opera a plataforma e cada cliente é um tenant do produto Flow4Food.

---

## 6. Exclusões de escopo (V1)

Fora do escopo da V1 — **não** projetar tabelas, rotas ou UI para:

- Roteamento de impressão por setor (bar/cozinha).
- KDS avançado / tela de cozinheiro.
- Cardápio por QR Code.
- Módulo fiscal (NFC-e / SAT).
- Catálogo dinâmico de permissões (perfis fixos permanecem na V1; dinâmico é V2 — ver `v2-melhorias.md`).
- Histórico de auditoria **visual**: na V1 mantém-se apenas o registro bruto em `eventos_comanda`. Tela de visualização de auditoria fica fora de escopo.

---

## 7. Ordem de implementação recomendada (V1)

1. Tabela `tenants` (banco comercial começa limpo — sem migração de dados de teste).
2. `tenant_id` + RLS nas tabelas operacionais **e em `profiles`/`profile_permissions`**; injeção via `SET app.tenant_id` no `get_db`; role PG sem `BYPASSRLS`.
3. `system_users.tenant_id` + e-mail `UNIQUE` global + virada de chave no cadastro (onboarding atômico com clone dos perfis padrão + herança de tenant em funcionários).
4. `tenant_id` e `subscription_status` no JWT (login + refresh) + tratamento de `402` no Frontend (Admin → tela de pagamento; demais → aviso de suspensão).
5. Tabelas de billing (`planos`, `assinaturas`, `pagamentos_assinatura`) + `require_active_subscription` + job de vencimento.
6. Auditoria de Caixa (`caixa_sessoes`, `caixa_movimentos`) — §4.
7. (Paralelo, mesmo PR do passo 2) Corrigir race de estoque com `FOR UPDATE` e padronizar `increment_version` em todas as mutações de comanda.
8. Rebranding Matchpoint → Flow4Food (§5).

> Passos 1–3 são refactor estrutural que toca todas as queries (inclui tirar o `TENANT_ID = 1` hardcoded de `users_service`/`profiles_service`/`auth_service`) — quanto mais código acumular, mais caro fica. Priorizar.

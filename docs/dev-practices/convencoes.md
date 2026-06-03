# Convenções de Desenvolvimento

## Commits

Seguimos **Conventional Commits**. Formato:

```
<tipo>(<escopo opcional>): <descrição curta>

<corpo opcional>
```

### Tipos

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Documentação |
| `refactor` | Refatoração sem mudança de comportamento |
| `test` | Adicionar ou corrigir testes |
| `chore` | Tarefas de manutenção (deps, config) |
| `perf` | Melhoria de performance |
| `migration` | Migration de banco de dados |

### Exemplos

```
feat(comandas): add filtro por garçom na listagem
fix(auth): corrigir expiração de refresh token em timezone UTC
migration: add tenant_id em contas_pagar com RLS
docs: atualizar onboarding com setup do PostgreSQL 18
```

## Branches

```
main              → produção
staging           → pré-produção
development       → integração
feature/<nome>    → features individuais
fix/<nome>        → correções de bug
migration/<nome>  → migrations complexas que precisam de revisão
```

Nomes em kebab-case, descritivos:
```
feature/relatorio-cmv-por-periodo
fix/comanda-fecha-sem-pagamento
migration/add-modulo-notificacoes
```

## Python (Backend)

### Style

- Formatação: **ruff** (line-length 100, configurado em `pyproject.toml`)
- Tipos: **mypy** strict em código novo
- Imports: ordenados por ruff (`isort` integrado)

```python
# Correto — tipos explícitos em funções públicas
def get_user(user_id: int, db: Session) -> UserResponse:
    ...

# Correto — Optional explícito
def find_user(email: str, db: Session) -> User | None:
    ...
```

### Nomenclatura

| Elemento | Convenção | Exemplo |
|---|---|---|
| Arquivo | `snake_case` | `comanda_service.py` |
| Classe | `PascalCase` | `ComandaService` |
| Função/método | `snake_case` | `get_comanda_by_id` |
| Variável | `snake_case` | `total_valor` |
| Constante | `SCREAMING_SNAKE` | `MAX_RETRY_COUNT` |
| Schema Pydantic | `PascalCase` + sufixo | `ComandaCreate`, `ComandaResponse` |

### Estrutura de endpoint (padrão do projeto)

```python
@router.get("/{comanda_id}", response_model=ComandaResponse)
async def get_comanda(
    comanda_id: int,
    db: Session = Depends(get_tenant_db),      # sempre get_tenant_db, não get_db
    current_user: SystemUser = Depends(get_current_user),
) -> ComandaResponse:
    return comanda_service.get_by_id(db, comanda_id)
```

**Importante:** Sempre usar `get_tenant_db` (não `get_db`) em endpoints que acessam dados de tenant. `get_tenant_db` é quem configura o RLS.

## TypeScript (Frontend)

### Style

- Formatação: **ESLint** + TypeScript strict (configurado em `tsconfig.json`)
- Zero warnings no lint (`--max-warnings 0`)

### Nomenclatura

| Elemento | Convenção | Exemplo |
|---|---|---|
| Arquivo componente | `PascalCase` | `ComandaCard.tsx` |
| Arquivo hook | `camelCase` com `use` | `useComandas.ts` |
| Arquivo util/lib | `camelCase` | `formatCurrency.ts` |
| Componente | `PascalCase` | `ComandaCard` |
| Hook | `camelCase` com `use` | `useComandas` |
| Variável/função | `camelCase` | `totalValor` |
| Constante | `SCREAMING_SNAKE` | `MAX_ITEMS_PER_PAGE` |
| Type/Interface | `PascalCase` | `ComandaItem` |

### Padrão de feature

```
src/features/<nome>/
  ├── <Nome>Page.tsx          # página principal
  ├── <Nome>Form.tsx          # formulário (se houver)
  ├── use<Nome>.ts            # hook de dados (TanStack Query)
  └── schemas.ts              # Zod schemas de validação
```

### TanStack Query — padrão

```typescript
// Hook de listagem
export function useComanadas() {
  return useQuery({
    queryKey: ['comandas'],
    queryFn: () => api.get<Comanda[]>('/api/comandas').then(r => r.data),
  })
}

// Mutation com invalidação
export function useFecharComanda() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.post(`/api/comandas/${id}/fechar`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comandas'] }),
  })
}
```

## Pull Requests

### Checklist antes de abrir PR

- [ ] CI passa localmente (`ruff`, `mypy`, `tsc`, `eslint`)
- [ ] Se há migration: testou `alembic upgrade head` + `downgrade -1` + `upgrade head` do zero
- [ ] Sem `console.log` de debug no frontend
- [ ] Sem credenciais ou segredos commitados
- [ ] Título do PR segue Conventional Commits

### Tamanho ideal de PR

- Máximo ~400 linhas alteradas
- Uma feature por PR
- Migrations em PR separado quando complexas

### PR para `main`

Requer aprovação explícita e CI passando. Verificar antes:
- [ ] Feature validada em staging
- [ ] Migration testada em staging do zero
- [ ] Cliente avisado se houver impacto (downtime, re-login, etc.)

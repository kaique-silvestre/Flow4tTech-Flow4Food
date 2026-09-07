Status: ready-for-agent

# Reestruturação da Sidebar (Matchpoint)

## Problem Statement

A sidebar atual (`Sidebar.tsx`) não tem identidade visual da empresa (tenant) no topo — o espaço fica vazio, sem letra, nome ou nenhum indício de qual empresa está logada. O topbar mostra um título estático fixo ("Flow4Food") em vez de indicar em que página o usuário está dentro da empresa. O botão de colapsar/expandir a sidebar ocupa uma linha inteira no topo dela, competindo por espaço com o conteúdo de navegação. Grupos com submenu (Vendas, Estoque etc.) sempre abrem como flyout flutuante (portal), mesmo com a sidebar totalmente expandida — quando expandida, um accordion inline seria mais natural e ocuparia o espaço já disponível. "Configurações" vive misturado no meio da lista rolável de navegação, e o logout só existe escondido no dropdown do avatar do topbar, sem atalho direto na sidebar.

## Solution

Reestruturar `Sidebar.tsx`, `navConfig.ts`, `Topbar.tsx`, `Breadcrumb.tsx` e `AppLayout.tsx` para:
1. Adicionar bloco "Empresa" no topo da sidebar: quadrado com a letra inicial do tenant + nome + status da assinatura, estático (sem indicar que é clicável).
2. Adicionar campo de busca/filtro local logo abaixo do bloco Empresa, filtrando os itens de navegação por texto (sem chamada ao backend).
3. Agrupar os itens de navegação sob headings de seção (Operação / Gestão), com dois itens soltos no topo sem heading.
4. Trocar o flyout por accordion inline quando a sidebar está expandida; manter o flyout apenas no modo colapsado (rail de ícones), onde não há espaço para o accordion.
5. Fixar "Configurações" e "Sair" num rodapé não-rolável da sidebar, fora da lista de navegação principal.
6. Mover o botão de colapsar/expandir para um handle flutuante na borda da sidebar, em vez da barra de topo atual.
7. Substituir o título estático do topbar por um breadcrumb "Empresa / Página Atual" (sempre 2 níveis, inclusive em rotas raiz como Dashboard).
8. Expor `tenant_name` no JWT (login e refresh) para alimentar o bloco Empresa, já que hoje o token só carrega `tenant_id`.

## User Stories

1. Como usuário logado, quero ver o nome e a inicial da minha empresa no topo da sidebar, para confirmar rapidamente em qual empresa estou trabalhando (relevante em ambientes com múltiplos tenants/dispositivos compartilhados).
2. Como usuário logado, quero ver o status da minha assinatura (ex: "Ativa", "Trial") como subtítulo do bloco Empresa, para ter essa informação visível sem precisar entrar em Configurações.
3. Como usuário, quero que o bloco Empresa não pareça clicável (sem seta, sem hover de botão), para não tentar clicar em algo que não faz nada — hoje o sistema não permite trocar de empresa numa mesma sessão.
4. Como usuário, quero digitar parte do nome de uma tela no campo de busca da sidebar e ver só os itens que batem, para achar uma tela rapidamente sem escanear o menu inteiro visualmente.
5. Como usuário, quero que a busca da sidebar funcione client-side, instantânea, sem esperar uma resposta de rede, para não ter latência percebida.
6. Como usuário, quero ver os itens do menu agrupados em "Operação" (Cardápio, Vendas, Compras, Estoque) e "Gestão" (Financeiro, Relatórios, Cadastros), com Dashboard e Calendário soltos no topo, para navegar por contexto de uso em vez de uma lista plana.
7. Como usuário com a sidebar expandida, quero que clicar num grupo (ex: Vendas) expanda os subitens inline, embaixo do próprio grupo, para não perder o contexto visual saindo pra um flyout.
8. Como usuário com a sidebar colapsada (rail de ícones), quero que clicar num grupo ainda abra um flyout ao lado, já que não há espaço pra texto no rail.
9. Como usuário, quero ver "Configurações" e "Sair" sempre visíveis no rodapé da sidebar, separados visualmente do resto do menu, para não precisar rolar a lista de navegação pra encontrá-los.
10. Como usuário sem permissão em nenhuma tela de configurações (nem `configuracoes` nem `gestao_usuarios`), quero que o item "Configurações" simplesmente não apareça no rodapé, mantendo o mesmo comportamento de ocultação por permissão que o resto do menu já tem hoje.
11. Como usuário, quero que "Sair" no rodapé da sidebar encerre minha sessão do mesmo jeito que o "Sair" do dropdown do avatar no topbar (mesmo fluxo de logout, sem duplicar lógica).
12. Como usuário, quero clicar num handle pequeno na borda da sidebar pra colapsar/expandir, em vez de uma barra ocupando uma linha inteira no topo do menu, para ganhar espaço vertical de navegação.
13. Como usuário com a sidebar colapsada, quero que o handle mude de direção (seta pra abrir) pra eu saber que clicar nele expande de novo.
14. Como usuário, quero que a preferência de colapsado/expandido continue sendo lembrada entre sessões (como já funciona hoje via `localStorage`), mesmo com o botão mudando de lugar.
15. Como usuário em qualquer página (incluindo Dashboard, que hoje não mostra breadcrumb nenhum), quero ver "NomeDaEmpresa / NomeDaPágina" no topo, para ter contexto de onde estou sempre visível, não só em subtelas.
16. Como usuário numa subtela de grupo (ex: Estoque > Movimentos), quero ver só "NomeDaEmpresa / Movimentos" (2 níveis, sem o grupo pai "Estoque"), para manter o breadcrumb curto e consistente com o resto do sistema.
17. Como usuário em dispositivo mobile, quero que o menu continue abrindo como overlay deslizante pelo hambúrguer do topbar (comportamento atual inalterado), já que o handle flutuante de colapso é conceito exclusivo do modo desktop.
18. Como desenvolvedor, quero que `tenant_name` venha no payload do JWT tanto no login quanto no refresh, para o frontend nunca ficar com um token "velho" sem o nome da empresa depois de um refresh.
19. Como desenvolvedor, quero que adicionar `tenant_name` ao token não quebre nenhum consumidor existente do payload (é campo aditivo, não substitui nenhum campo atual).
20. Como usuário com badges dinâmicos ativos (ex: comandas abertas em Vendas, insumos críticos em Estoque, contas urgentes em Financeiro), quero que os badges continuem aparecendo do jeito que aparecem hoje, tanto no accordion expandido quanto no flyout colapsado, já que a lógica de contagem não muda nesta spec.
21. Como usuário com a sidebar colapsada, quero que o bloco Empresa encolha pra só a letra (sem nome/subtítulo cortado ou quebrando layout), e que o campo de busca simplesmente desapareça até eu expandir de novo.
22. Como usuário navegando numa tela que não está listada no menu (ex: detalhe de um cadastro específico), quero ver ao menos o nome da minha empresa no topbar, mesmo sem um segundo segmento de página, em vez de um breadcrumb quebrado ou com um label inventado.

## Implementation Decisions

### Backend (`auth_service.py`)

- `_build_token_response()` (login) e `rotate_refresh_token()` (refresh): ambos hoje montam o dict do payload JWT de forma duplicada. Adicionar `"tenant_name": tenant.nome_fantasia` em ambos, buscando o tenant via `tenant_repository.get_tenant_by_id(db, user.tenant_id)` (função já existente, mesmo padrão usado hoje pra `assinatura`/`subscription_status`).
- Campo aditivo — não altera nenhum campo existente do payload, não é breaking change.
- Frontend: `AuthUser` (interface em `authStore.ts`) ganha `tenant_name: string` — vem só do decode do JWT, sem nova chamada de rede (mesmo padrão que já existe pra `subscription_status`).

### Frontend — `Sidebar.tsx` / `navConfig.ts`

- **Bloco Empresa**: novo subcomponente no topo da sidebar. Quadrado `rounded-md`, cor sólida (ex: `bg-primary` ou equivalente do tema atual), letra = primeira letra de `user.tenant_name`. Nome completo ao lado/abaixo, truncado se longo. Subtítulo = label amigável do status da assinatura, reaproveitando `SUBSCRIPTION_STATUS_LABELS` (hoje em `frontend/src/features/platform/subscriptionStatus.ts`, usado só no admin de plataforma — promover import pro contexto tenant, sem duplicar o mapa). Sem chevron, sem `cursor-pointer`, sem hover de botão — puramente informativo.
- **Busca local**: campo de texto abaixo do bloco Empresa. Nova função pura exportada `filterNavItems(query: string, items: NavItem[]): NavItem[]` em `navConfig.ts` (ou módulo irmão) — filtra por `label` do item pai OU de qualquer filho (case-insensitive, sem acento-sensível não é requisito aqui). Item pai aparece na lista filtrada se ele mesmo bate OU se algum filho bate (nesse caso, mostra só os filhos que batem). Sem debounce necessário — filtro é sobre lista já em memória (< 20 itens), não há custo de performance a mitigar.
- **Headings de seção**: `NavItem`/`NAV_ITEMS` em `navConfig.ts` ganha reorganização em grupos com heading opcional:
  - Sem heading: Dashboard, Calendário
  - `"OPERAÇÃO"`: Cardápio, Vendas, Compras, Estoque
  - `"GESTÃO"`: Financeiro, Relatórios, Cadastros
  - Fora da lista principal (rodapé, ver abaixo): Configurações
  - Modelo de dados: introduzir `NavGroup { heading?: string; items: NavItem[] }[]` substituindo o array flat `NAV_ITEMS` (ou mantendo `NAV_ITEMS` como está e adicionando um array derivado `NAV_GROUPS` — decisão de implementação, mas o heading precisa existir no dado, não só no JSX).
- **Accordion vs flyout**: comportamento dual, decidido no grill:
  - Sidebar expandida: grupo com filhos expande **inline** (accordion, abre embaixo do próprio item), reaproveitando a técnica de altura animada via CSS grid (`grid-rows-[0fr]` → `grid-rows-[1fr]`) do componente de referência trazido pelo usuário.
  - Sidebar colapsada (rail de ícones, comportamento **mantido** de hoje): grupo com filhos abre o **flyout** via portal que já existe (`renderFlyout` em `Sidebar.tsx`), sem mudanças nessa parte.
  - `openGroup`/estado de accordion e `openGroup`/estado de flyout podem compartilhar o mesmo state (`openGroup: string | null`), só mudando o que é renderizado (`inline` vs `portal`) conforme `collapsed`.
- **Rodapé fixo**: novo bloco não-rolável no final da sidebar (fora do `<nav className="overflow-y-auto">`), contendo:
  - "Configurações" (com seus filhos: Configurações Gerais, Usuários) — mesma lógica de visibilidade por permissão que já existe hoje (`visibleChildren`, filtra por `screen`/`usePermissions()`), só reposicionado. Expande/colapsa os filhos **reusando o mesmo mecanismo de accordion inline** usado pelos grupos da lista principal (Vendas, Estoque etc.) — não é um padrão de interação separado; clique em "Configurações" no rodapé se comporta igual a clicar em qualquer outro grupo com filhos.
  - "Sair" — chama a mesma função de logout que o dropdown do avatar do `Topbar.tsx` já usa (`clearToken` do `useAuthStore` + `navigate("/login")` + toast) — não duplicar a lógica, extrair um `handleLogout` compartilhado (hook ou função utilitária) usado nos dois lugares.
- **Handle de colapso**: botão pequeno, circular, grudado na borda direita da sidebar (posição vertical central), sempre visível independente do estado. Ícone `ChevronLeft`/`ChevronRight` (ou `PanelLeftClose`/`PanelLeftOpen`, mesmo ícone já usado no componente de referência) trocando de direção conforme `collapsed`. Substitui o `<button>` de linha inteira que existe hoje no topo do `<aside>` (`Sidebar.tsx`, bloco `hidden ... lg:flex` com ícone `Menu`). Visível só em desktop (`hidden lg:flex`, mesmo padrão de breakpoint já usado) — no mobile o menu continua controlado pelo hambúrguer do `Topbar.tsx` (`onMenuClick`), sem mudança.
- `localStorage` (`sidebar_collapsed`) e a prop `onToggle`/`collapsed` vindos de `AppLayout.tsx` continuam exatamente como estão — só muda o elemento visual que dispara `onToggle()`.
- **Modo colapsado (rail de ícones) — bloco Empresa e busca**: quando `collapsed=true`, o bloco Empresa encolhe pra mostrar só o quadrado com a letra (mesmo padrão que os itens de nav já aplicam a `item.label` hoje — esconder texto, manter ícone/símbolo). O campo de busca **some inteiramente** no rail (não há espaço pra digitar nem exibir texto) — reaparece ao expandir. Se havia um texto de busca digitado antes de colapsar, ele é preservado em memória (não reseta o filtro), só fica invisível até expandir de novo — evita perder o que o usuário tinha digitado.
- **Modo colapsado — rodapé**: "Configurações" e "Sair" seguem o mesmo tratamento icon-only que o resto do rail (ícone sem label, `title` com tooltip nativo do browser via atributo `title`, mesmo padrão já usado nos itens normais do rail hoje).

### Frontend — `Topbar.tsx` / `Breadcrumb.tsx`

- Remover o `<span className="font-semibold">Flow4Food</span>` estático do `Topbar.tsx`.
- Mover a renderização do breadcrumb pra dentro do `Topbar.tsx` (ela deixa de ser renderizada dentro de `<main>` no `AppLayout.tsx`).
- `buildCrumbs(pathname)` em `Breadcrumb.tsx`: hoje retorna `[]` (nada é mostrado) pra rotas de item raiz sem filhos (ex: Dashboard, Cardápio) — mudar pra **sempre** retornar pelo menos 2 níveis: `[{ label: tenant_name }, { label: <label da página atual> }]`. Pra grupos com filho, manter a lógica de dedup já existente ("Compras > Compras" vira só "Compras") mas sempre prefixado pelo nome da empresa — nunca mostrar o grupo pai quando há filho (ex: "Estoque > Movimentos" vira "Empresa / Movimentos", não "Empresa / Estoque / Movimentos") — sempre exatamente 2 segmentos.
- Exportar `buildCrumbs` (hoje não-exportada) pra ser testável isoladamente sem montar o componente.
- `tenant_name` vem de `useAuthStore((s) => s.user?.tenant_name)`.
- **Fallback pra rota não reconhecida**: hoje `buildCrumbs` retorna `[]` (nada renderiza) quando o `pathname` não bate com nenhum item/filho de `NAV_ITEMS`. Com a regra de "sempre 2 níveis", esse caso passa a retornar só `["Empresa"]` (1 nível, sem segundo segmento) — nunca inventar um label de página que não existe no menu.

### Fora de escopo mas registrado

- Command palette / busca global (`⌘K`) — decidido no grill: não implementar agora, é feature nova maior; a busca desta spec é só filtro local dos itens já visíveis no menu.
- Trocar de empresa (multi-tenant switch) — sistema hoje é 1 login = 1 tenant; bloco Empresa é só informativo.

## Testing Decisions

Um bom teste aqui testa comportamento observável pelo usuário (o que aparece na tela dado um estado), não como o JSX está estruturado internamente.

- **Seam 1 — backend, `backend/tests/test_auth.py`** (seam já existente, decodifica o JWT após login/refresh): adicionar asserção de que `tenant_name` está presente e correto no payload decodificado, tanto no fluxo de login quanto no de refresh (os dois pontos que constroem o payload separadamente).
- **Seam 2 — frontend, lógica pura, novo arquivo de teste ao lado de `navConfig.ts` e `Breadcrumb.tsx`** (Vitest puro, sem RTL/DOM):
  - `filterNavItems`: dado um texto de busca, retorna só os itens (ou grupos com filho) que batem; case-insensitive; string vazia retorna tudo.
  - `buildCrumbs`: dado um `pathname` de rota raiz (ex: `/`), retorna `["Empresa", "Dashboard"]`; dado rota de subitem de grupo (ex: `/estoque/movimentos`), retorna exatamente 2 segmentos (`["Empresa", "Movimentos"]`), nunca 3.
- **Seam 3 — frontend, RTL, novo arquivo `Sidebar.test.tsx`** (prior art: `frontend/src/components/ElapsedTime.test.tsx` — Vitest + Testing Library, sem mocks de módulo, estado real): testar que o rodapé da sidebar ("Configurações", "Sair") aparece/desaparece corretamente conforme a permissão do usuário logado. Seedar `useAuthStore` diretamente via `useAuthStore.setState({ user: { ...permissions: [...] } })` (loja real, sem mock de hook) e verificar:
  - Usuário com `permissions` incluindo `"configuracoes"` OU `"gestao_usuarios"`: item "Configurações" aparece no rodapé.
  - Usuário sem nenhuma das duas permissões: item "Configurações" não aparece no rodapé (mas "Sair" continua aparecendo sempre, já que logout não depende de permissão de tela).
  - Usuário com só `"gestao_usuarios"` (sem `"configuracoes"`): "Configurações" aparece, mas expandir mostra só o filho "Usuários", não "Configurações Gerais" (reaproveita a lógica de `visibleChildren` já existente, só verificando que a permissão granular por filho continua funcionando após a mudança de posição pro rodapé).
  - "Sair" está sempre presente e dispara a função de logout compartilhada quando clicado.
- Não é necessário teste E2E/Playwright — não há suite E2E no projeto hoje; os 3 seams acima cobrem o comportamento novo sem depender de infraestrutura nova.

## Out of Scope

- Command palette / busca global com atalho `⌘K` — só filtro local de texto nesta spec.
- Troca de empresa (multi-tenant switcher) — bloco Empresa é estático/informativo.
- Migração de ícones ou biblioteca de UI — continua usando `lucide-react`, já instalado.
- Qualquer mudança em `usePermissions`/`useFeatureFlags`/lógica de badges dinâmicos (contagens de Vendas/Estoque/Financeiro) — reaproveitados como estão.
- Responsividade/overlay mobile — comportamento atual mantido sem alteração.
- Renomear ou reorganizar rotas/URLs — só a apresentação/agrupamento visual do menu muda, nenhuma rota muda de path.
- Testes de snapshot visual/regressão de CSS do accordion ou do handle flutuante — comportamento puramente de apresentação, não coberto por teste automatizado nesta spec (validação visual manual).

## Further Notes

- Grill de pré-implementação realizado (skills `grilling` + `domain-modeling`). Conflito de glossário identificado e resolvido: `CONTEXT.md` já definia **Tenant** com `_Avoid_: ...organização, conta`; decisão registrada no próprio `CONTEXT.md` de que a label de UI pro tenant é **"Empresa"** (não "Organização", que o usuário cogitou e descartou na própria frase).
- Componente de referência trazido pelo usuário (`dashboard-sidebar.tsx`/`demo.tsx`, shadcn-style, Tailwind, `lucide-react`) serviu de inspiração visual (accordion via CSS grid, bloco de identidade quadrado, badges, rodapé fixo) — não foi copiado literalmente; adaptado ao stack e dados reais do Matchpoint (permissões, feature flags, badges dinâmicos, RLS multi-tenant) que o componente de referência não tem.
- Decisões tomadas por delegação explícita do usuário ("se você achar interessante e não afetar performance"): busca local simples em vez de command palette; agrupamento em headings "Operação"/"Gestão" proposto por mim e aceito sem alteração.

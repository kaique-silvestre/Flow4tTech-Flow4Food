Status: ready-for-agent

# Reestruturação de Gestão de Usuários (Matchpoint)

## Problem Statement

A tela `/configuracoes/usuarios` (`GestaoUsuariosPage.tsx`) tem duas abas — Usuários e Perfis — e alguns atritos:

1. As tabelas de Usuários e Perfis usam `<table>` cru com convenções próprias (badges de status como `<span>` inline, sem componente compartilhado), diferentes das tabelas já padronizadas em Cardápio/Estoque/Movimentos (ver `.scratch/cardapio-restructure/spec.md`).
2. A linha de usuário não tem nenhum elemento visual de identidade (avatar/inicial) — só texto corrido, difícil de escanear numa lista longa.
3. As ações (Editar/Desativar) são dois botões soltos lado a lado — em telas com mais ações por linha (ex. um dia "Redefinir senha", "Ver permissões"), isso não escala; um menu de ações resolveria melhor.
4. O front permite tentar trocar o próprio Perfil no `UserModal` mesmo sendo o usuário logado — a regra "usuário não pode alterar o próprio perfil" já existe no backend (`users_service.py::update_existing_user`, retorna 409 "Não pode alterar o próprio perfil"), mas o front não desabilita o campo, então o usuário só descobre a regra ao ver um erro depois de tentar salvar.
5. Mesmo problema num segundo lugar: quando um usuário está "sem perfil" (`profile_id` null), o `UserModal` mostra uma grade de checkboxes de permissões individuais (`screens`). `users_service.py::set_user_permissions` bloqueia **incondicionalmente** alterar as próprias permissões (`user_id == current_user_id` → 409 "Não pode alterar as próprias permissões") — inclusive pro Proprietário — mas o front deixa marcar/desmarcar normalmente e só falha ao salvar.
6. Terceiro caso: `users_service.py::update_existing_user` bloqueia **qualquer** edição de um usuário `is_owner` feita por outra pessoa (409 "Usuário proprietário não pode ser alterado por outros") — não só o perfil, qualquer campo. Hoje o front só esconde o botão "Desativar" pro Proprietário; o botão "Editar" continua aberto pra qualquer admin, que preenche o modal inteiro e só descobre a regra no 409 ao salvar.
7. A aba ativa (Usuários/Perfis) é `useState` local — trocar de aba não muda a URL, mesmo problema já identificado e corrigido em `/estoque/movimentos` (ver spec do Cardápio).

## Solution

Reestruturar `/configuracoes/usuarios` em quatro frentes, usando os termos do glossário do projeto (Usuário, Perfil — ver `CONTEXT.md`, entradas adicionadas nesta sessão):

1. **Migrar as duas tabelas (Usuários, Perfis) para `components/ui/table.tsx`** (o mesmo componente decidido e já em construção pela spec do Cardápio) — mesma convenção de alinhamento e hover já fixada lá.
2. **Avatar de iniciais na coluna de usuário**: um círculo com as iniciais do nome (mesmo cálculo `getInitials` do exemplo de referência), sem foto/upload — não existe campo de foto no modelo de usuário hoje, e não é objetivo desta spec criar um.
3. **Badge de status reaproveitando `components/ui/badge.tsx`** (já instalado, usado em `notifications.tsx`/`announcement.tsx`) no lugar dos `<span>` inline com classes repetidas em Usuários e Perfis.
4. **Ações em dropdown (`components/ui/dropdown-menu.tsx`, já instalado)**: substitui os botões soltos "Editar"/"Desativar" por um único menu de ações por linha, preparado para crescer (mais itens no futuro) sem precisar redesenhar a linha.
5. **As três proteções do backend refletidas no front** (nenhuma regra nova, só espelhar o que `users_service.py` já impõe, pra virar impedimento visível em vez de erro depois de tentar):
   - `UserModal` desabilita o campo de Perfil (com explicação) quando o usuário está editando a si mesmo.
   - `UserModal` desabilita a grade de checkboxes de permissões (`screens`) quando o usuário está editando a si mesmo — mesma regra, outro campo, incondicional (vale pro Proprietário também).
   - A ação "Editar" fica desabilitada (não só "Desativar") na linha de um usuário `is_owner` quando quem está olhando não é esse mesmo Proprietário — hoje só a ação de desativar tinha essa guarda, editar não.
6. **Aba ativa via query param** (`?tab=usuarios` | `?tab=perfis`, via `useSearchParams`) — mesmo padrão decidido para `/estoque/movimentos`, endereçável e compatível com o botão voltar do navegador. Breadcrumb "Configurações > Usuários" já funciona hoje (item estático em `NAV_ITEMS`) e não muda.

## User Stories

1. Como administrador, quero ver as iniciais de cada usuário num círculo ao lado do nome, para escanear a lista mais rápido.
2. Como administrador, quero que o status (Ativo/Inativo) de usuário e perfil use o mesmo componente de badge do resto do sistema, para não ver mais um estilo de pílula diferente.
3. Como administrador, quero um menu de ações por usuário/perfil em vez de botões soltos, para a tela ter espaço pra crescer com novas ações sem virar uma fileira de botões.
4. Como administrador, quero que o campo de Perfil no modal de edição fique desabilitado quando estou editando a mim mesmo, para entender a restrição antes de tentar salvar e falhar.
5. Como administrador, quero uma explicação curta (tooltip ou texto de apoio) no campo de Perfil desabilitado, para saber *por que* não posso mudar, não só que não posso.
6. Como administrador, quero copiar o link da aba "Perfis" e a pessoa que abrir cair direto nela, para não precisar explicar "clica em Perfis".
7. Como administrador, quero que o botão voltar do navegador desfaça a troca entre Usuários e Perfis, para a navegação se comportar como eu já espero.
8. Como desenvolvedor, quero reaproveitar `components/ui/badge.tsx` e `components/ui/dropdown-menu.tsx` (já instalados) em vez de instalar `@radix-ui/react-avatar`/`@radix-ui/react-checkbox`/etc. do exemplo externo, para não duplicar dependências que o projeto já tem resolvidas de outro jeito.
9. Como desenvolvedor, quero que as tabelas de Usuários e Perfis usem o mesmo `components/ui/table.tsx` das outras telas já padronizadas, para manter uma única fonte de verdade de estilo de tabela no app.
10. Como administrador, quero que a badge "Proprietário" (usuário `is_owner`) e a coluna "Sistema" (perfil `is_system`) continuem visíveis como hoje, para não perder informação que já existe.
11. Como desenvolvedor, quero que o termo "Usuário" e "Perfil" estejam definidos em `CONTEXT.md`, para ter vocabulário fechado antes de mexer nessas telas.
12. Como administrador (inclusive Proprietário), quero que a grade de permissões individuais fique desabilitada quando estou editando minhas próprias permissões, para não marcar/desmarcar algo que vai falhar ao salvar.
13. Como administrador, quero que o botão "Editar" de outro usuário Proprietário fique desabilitado (não só "Desativar"), para não preencher um formulário inteiro só pra descobrir no final que a edição é bloqueada.
14. Como administrador, quero uma explicação curta em cada um dos três controles bloqueados (perfil, permissões, editar-de-terceiro), para entender a razão específica de cada bloqueio, não um erro genérico.

## Implementation Decisions

- **Tabela**: `GestaoUsuariosPage.tsx` migra as duas tabelas (`<table>` de Usuários e de Perfis) para `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx` — mesmo componente da spec do Cardápio (depende dela existir primeiro, ou é construído em paralelo se esta spec for implementada antes — o componente em si é código novo sem dependência de ordem, só não duplicar a criação).
- **Avatar de iniciais**: componente local pequeno (`UserAvatarInitials` ou similar, em `features/configuracoes/usuarios/`), círculo colorido (`bg-primary/10 text-primary` ou equivalente à paleta do projeto) com `getInitials(nome)` — mesma função do exemplo de referência (split por espaço, primeira letra de cada parte, uppercase, join). Sem `@radix-ui/react-avatar` — não precisa de `AvatarImage`/fallback assíncrono já que nunca há imagem.
- **Badge**: trocar os `<span className="rounded-full px-2 py-0.5 ...">` por `<Badge variant="outline" className="...">` (cores de sucesso/neutro via `className`, o componente já aceita override). Aplicar tanto no status de Usuário quanto de Perfil.
- **Dropdown de ações**:
  - Usuários: itens "Editar" e "Desativar"/"Ativar" (label muda conforme `is_active`, como hoje) dentro do dropdown; mesma lógica de ocultar "Desativar" quando `isSelf || user.is_owner` é preservada (agora como item ausente do menu, não botão ausente).
  - Perfis: itens "Editar"/"Ver" (rótulo já condicional a `profile.name === "Admin"`, preservado) e "Desativar"/"Ativar" (com `disabled` quando `!canToggle`, preservado — perfil Admin ou perfil com usuários não pode ser desativado).
  - Sem novos itens de menu nesta spec (ex. "Redefinir senha") — a spec só troca o container de dois botões pra um menu, não adiciona ação nova.
- **As três proteções do backend refletidas no front** (todas espelham regra já existente em `users_service.py`, nenhuma mudança de backend):
  - `UserModal.tsx`: quando `editing` é o usuário logado (`currentUser?.user_id === editing.id`, mesmo `isSelf` já calculado em `GestaoUsuariosPage.tsx` — passar como prop ou recalcular no modal), o campo de Perfil (`select` de `profile_id`) fica `disabled`, com texto de apoio: "Você não pode alterar seu próprio perfil".
  - Mesmo `isSelf`: a grade de checkboxes de `screens` (visível quando `profile_id` é null) fica com todos os inputs `disabled`, com texto de apoio: "Você não pode alterar suas próprias permissões" — espelha `set_user_permissions` (bloqueio incondicional, vale pro Proprietário também, não é exceção do `is_owner`).
  - `GestaoUsuariosPage.tsx`: a ação "Editar" no dropdown de um usuário fica `disabled` quando `user.is_owner && !isSelf` (o mesmo par de condições já usado pra esconder "Desativar", só que agora também guarda "Editar") — com texto de apoio no próprio item do menu ou tooltip: "Usuário proprietário só pode ser editado por si mesmo". Quando é o próprio Proprietário editando a si mesmo, "Editar" continua liberado (ele pode mudar nome/email/username, só não o próprio perfil/permissões, cobertos pelos dois pontos acima).
- **Aba via query param**: mesmo padrão da decisão em `MovimentosPage.tsx` — `useSearchParams`, default `"usuarios"`, trocar de aba chama `setSearchParams`.

## Testing Decisions

- Testes cobrem comportamento externo: avatar mostra iniciais corretas para nomes com 1 e 2+ palavras, badge de status reflete `is_active`, dropdown de ações esconde/desabilita itens certos por `isSelf`/`is_owner`/`is_system`/`user_count`, campo de Perfil desabilitado quando editando a si mesmo, grade de permissões desabilitada quando editando as próprias permissões, ação "Editar" desabilitada para Proprietário visto por outro usuário (e habilitada quando é o próprio Proprietário), troca de aba reflete no query param.
- Extensão de testes existentes (se houver) de `GestaoUsuariosPage`/`UserModal`/`ProfileModal` — não criar arquivo de teste novo do zero se já existir cobertura para essas páginas; seguir o padrão de mock já usado ali.
- `components/ui/table.tsx`, `components/ui/badge.tsx`, `components/ui/dropdown-menu.tsx` não precisam de teste próprio (já existem ou já são componentes de apresentação cobertos indiretamente).
- Sem mudança de backend nesta spec (a regra de "não pode alterar o próprio perfil" já existe e é só espelhada no front) — nenhum teste backend novo necessário.

## Out of Scope

- Upload de foto de usuário (campo novo no backend, storage) — avatar é só iniciais nesta spec.
- Checkboxes de seleção em massa / ações em lote (bulk actions) — não existe hoje, não foi pedido, não faz sentido pro tamanho típico de uma lista de usuários de um tenant.
- Coluna "Two-Step" (autenticação de dois fatores) — não existe no domínio do sistema hoje; se um dia existir, é spec própria com mudança de backend.
- Novos itens no menu de ações (ex. "Redefinir senha", "Ver permissões", "Histórico de login") — a spec só reorganiza os itens que já existem em um menu.
- Coluna "Last Login" / "Joined Date" do exemplo de referência — `UserResponse` já tem `last_login`/`created_at`, mas adicioná-las à tabela não foi pedido; registrar como ideia futura, não implementar agora.
- Mudança no modelo de permissões de Perfil (as 8 permissões existentes, a tela de edição de permissões em si) — fora de escopo, esta spec é só lista + modal de usuário.

## Further Notes

Esta spec nasceu de uma sessão de discussão comparando `/configuracoes/usuarios` com um componente de tabela de referência externo (avatar + badge + dropdown de ações, estilo shadcn) colado pelo usuário. Decisões chave:
- O componente de referência tinha `Two-Step`, checkboxes de seleção e fotos de usuário — nenhum desses faz sentido no domínio atual do Matchpoint; usuário confirmou explicitamente descartar os três.
- Achado importante durante a investigação: **três** proteções (não uma) já existem no backend — `users_service.py::update_existing_user` bloqueia auto-alteração de perfil E bloqueia qualquer edição de um Proprietário por outra pessoa; `users_service.py::set_user_permissions` bloqueia auto-alteração de permissões incondicionalmente. O pedido do usuário por "um padrão pra admin não poder se remover de admin" já está resolvido no servidor nas três frentes; o trabalho real é só o front parar de deixar a pessoa tentar e falhar, desabilitando os três controles certos com explicação. A segunda e a terceira proteção só apareceram numa segunda passada pelo código, depois que o usuário perguntou "faltou algo?" — a primeira leitura do `users_service.py` só tinha pego a checagem de perfil.
- `components/ui/badge.tsx` e `components/ui/dropdown-menu.tsx` já estavam instalados no projeto antes desta spec (usados em `notifications.tsx`/`announcement.tsx`) — decisão explícita de reaproveitá-los em vez de instalar as dependências do componente de referência externo (`@radix-ui/react-avatar`, `@radix-ui/react-checkbox`, etc.).
- `CONTEXT.md` ganhou as entradas "Usuário" e "Perfil" nesta sessão — termos não existiam no glossário antes, apesar de já serem usados pelo código.
- Esta spec é separada da spec do Cardápio (`.scratch/cardapio-restructure/spec.md`) por ser uma área de domínio diferente (Usuário/Perfil/permissões, não Cardápio/Estoque) — mas reaproveita o mesmo `components/ui/table.tsx` decidido lá, e replica a mesma decisão de query param pra abas já tomada para `/estoque/movimentos`.

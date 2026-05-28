# PRD — Responsividade Mobile (Matchpoint)

## Problem Statement

O sistema Matchpoint é usado por garçons em campo com celular durante o atendimento. As telas principais (listagem de comandas, comanda aberta, fechamento) não funcionam em telas menores que 1024px: o painel lateral ocupa espaço fixo e não colapsa, a tela de comanda aberta tem um painel de 320px fixo que quebra em mobile, e as tabelas transbordam horizontalmente sem controle. O gerente, que usa PC para gestão, não é impactado — mas o garçom, que opera o sistema no momento mais crítico do negócio, usa uma interface inutilizável no celular.

## Solution

Tornar responsivo o fluxo operacional do garçom (v1): navegação lateral vira drawer em mobile, a tela de comanda aberta ganha layout adaptado com bottom sheet para o carrinho, e as demais telas do fluxo (listagem de comandas, fechamento) recebem ajustes de grid e tabela. Tamanho mínimo garantido: 375px. Telas de cadastro e relatórios ficam fora do escopo desta versão.

## User Stories

1. Como garçom, quero acessar o sistema no meu celular (375px+), para que eu não precise de um tablet ou computador durante o atendimento.
2. Como garçom, quero um botão de menu visível no topo da tela em mobile, para que eu possa navegar entre seções sem precisar de sidebar permanente.
3. Como garçom, quero que o menu lateral deslize da esquerda como um drawer com overlay escuro, para que eu entenda que é uma camada temporária sobre o conteúdo.
4. Como garçom, quero que o drawer feche automaticamente ao clicar em uma rota, para que eu não precise fechar manualmente a cada navegação.
5. Como garçom, quero que o drawer feche ao clicar no overlay escuro fora dele, para que fechar seja intuitivo.
6. Como garçom, quero ver a lista de comandas abertas em cards organizados em 2 colunas no celular, para que caibam mais comandas na tela sem precisar rolar muito.
7. Como garçom, quero abrir uma comanda e ver o cardápio ocupando toda a tela do celular, para que os produtos sejam legíveis e fáceis de tocar.
8. Como garçom, quero ver os produtos do cardápio em grade de 2 colunas no celular, para que o tamanho dos cards seja adequado para toque.
9. Como garçom, quero um botão flutuante no rodapé que indica quantos itens estão na comanda e o total, para que eu saiba o estado da comanda sem sair do cardápio.
10. Como garçom, quero que ao clicar no botão flutuante abra um bottom sheet com os itens da comanda, para que eu revise e finalize sem perder o contexto do cardápio.
11. Como garçom, quero fechar o bottom sheet da comanda deslizando para baixo ou clicando fora, para que a interação seja fluida e natural.
12. Como garçom, quero que todos os botões de ação tenham área de toque mínima de 44px, para que eu não erre o toque com o polegar.
13. Como garçom, quero que a tela de fechamento de comanda funcione em mobile, para que eu finalize o atendimento pelo celular sem precisar de ajuda.
14. Como gerente, quero que o layout em desktop permaneça idêntico ao atual, para que minha experiência de gestão não seja afetada pela mudança.
15. Como gerente, quero que a sidebar em desktop continue fixada lateralmente com comportamento de colapso atual, para que a navegação em PC não mude.
16. Como garçom, quero que formulários em mobile sejam scrolláveis quando o teclado virtual aparecer, para que campos não fiquem escondidos atrás do teclado.
17. Como garçom, quero que filtros e buscas na listagem de comandas funcionem em mobile, para que eu encontre uma comanda específica rapidamente.
18. Como garçom, quero que a tela de comprovante/recibo funcione em mobile para impressão ou exibição ao cliente, para que o fechamento seja completo no celular.
19. Como garçom, quero que imagens e ícones de produtos no cardápio sejam nítidos em telas de alta densidade (Retina), para que a experiência visual seja adequada.
20. Como gerente, quero que o dashboard seja navegável em tablet (768px+) mesmo não sendo prioridade mobile, para que eu possa consultar KPIs sem abrir o computador.

## Implementation Decisions

### Módulos a modificar

**AppLayout + Sidebar (fundação — desbloqueia tudo)**
- Adicionar estado `isSidebarOpen` gerenciado por hook `useSidebar`
- Em `< lg`: sidebar vira `position: fixed`, z-index alto, largura `w-64`
- Overlay: `div` fixo com `bg-black/50` que fecha o drawer ao clicar
- Topbar: exibir botão hamburger (`Menu` icon) somente em `< lg`
- Sidebar fecha automaticamente ao mudar de rota (`useEffect` no `pathname`)
- Em `lg+`: comportamento atual preservado (colapso entre w-14 e w-52)

**ComandasPage**
- Cards: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-4` (atualmente sem breakpoints)
- Filtros/busca: `w-full` em mobile, `sm:w-auto` em desktop

**ComandaAbertaPage (maior refatoração)**
- Layout: `flex-col` em mobile, `flex-row` em `lg+`
- Painel esquerdo (`w-80` fixo → `w-full lg:w-80`): ocupa tela inteira em mobile
- Em mobile: painel direito (comanda) vira bottom sheet
- Bottom sheet: componente `BottomSheet` com `position: fixed`, `bottom-0`, `w-full`, altura configurável, `transform translate-y` animado
- Botão flutuante: `position: fixed`, `bottom-4 right-4`, exibe contagem de itens e total — só visível em mobile (`lg:hidden`)
- Grid de produtos: `grid-cols-2 sm:grid-cols-3 lg:grid-cols-4` (ajustar atual)
- Área de toque mínima: `min-h-[44px] min-w-[44px]` em botões de ação

**FechamentoPage / ComprovantePage**
- Revisar layout — garantir que inputs e botões empilham corretamente em mobile
- Campos de formulário: `w-full` em mobile

### Decisões técnicas

- Breakpoint primário de corte: `lg` (1024px) — abaixo é mobile, acima é desktop
- Tamanho mínimo garantido: 375px
- Nenhuma dependência nova — usar apenas Tailwind classes e React state
- `BottomSheet` extraído como componente isolado reutilizável
- Hook `useSidebar` centraliza estado e lógica de open/close/auto-close
- Sem bibliotecas de gestos (sem `framer-motion` ou `react-spring`) nesta versão — animações via Tailwind `transition`
- Telas de cadastro, relatórios e configurações: sem alteração nesta versão

### Schema / API
Nenhuma mudança de schema ou API — responsividade é puramente frontend.

## Testing Decisions

**O que torna um bom teste aqui:** testar comportamento observável pelo usuário, não implementação. Ex: "drawer abre ao clicar hamburger" não "estado `isSidebarOpen` vira true".

**Módulos a testar:**

- `useSidebar` hook — testar: abre, fecha, fecha ao mudar rota, fecha ao clicar overlay
- `BottomSheet` componente — testar: renderiza quando `open=true`, não renderiza quando `false`, chama `onClose` ao clicar overlay
- `ComandasPage` — testar que cards renderizam em grid responsivo (snapshot ou classe CSS)

**Prior art:** verificar testes existentes em `frontend/src` para padrão de teste de hooks e componentes.

## Out of Scope

- Telas de cadastro (Fornecedores, Insumos, Garçons, Categorias, Métodos de Pagamento) — uso exclusivo no PC
- Páginas de relatórios (DRE, CMV, Fechamento de Caixa, Vendas por Garçom etc.) — gestão, não operação
- EstoquePage e MovimentaçõesPage
- NovaCompraPage e ComprasPage
- ConfiguracoesPage
- App nativo (React Native / PWA) — esta versão é somente web responsivo
- Gestos de swipe no bottom sheet
- Suporte a browsers antigos (IE, Samsung Browser < v15)

## Further Notes

- Prioridade de execução: (1) AppLayout/Sidebar → (2) ComandaAbertaPage → (3) ComandasPage → (4) FechamentoPage/ComprovantePage
- `BottomSheet` deve ser genérico o suficiente para ser reutilizado futuramente em outras telas (ex: filtros mobile)
- Validar em Chrome DevTools com perfis: iPhone SE (375x667), iPhone 14 (390x844), iPad Mini (768x1024)
- Dashboard: `grid-cols-2 lg:grid-cols-4` já existe, gráficos recebem `h-48 md:h-64` — melhoria incremental, não bloqueante

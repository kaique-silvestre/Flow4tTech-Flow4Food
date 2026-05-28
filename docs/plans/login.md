Plano de Sistema de Autenticação e Permissões para Restaurante
1. Conceito Geral

Sistema com username + senha (não email)
Um administrador por estabelecimento
Usuários comuns com permissões customizadas
Administrador define exatamente o que cada usuário pode fazer

2. Estrutura de Usuários
Administrador

Criado no cadastro inicial do restaurante
Tem acesso total ao sistema
Único que pode criar/editar/excluir outros usuários
Único que pode atribuir/modificar permissões

Usuários Comuns

Criados pelo administrador
Cada um tem um conjunto específico de permissões
Permissões definidas recurso por recurso
Não podem criar outros usuários
Não podem modificar suas próprias permissões

3. Dados de Login
Cada usuário tem:

Nome completo (ex: "João Silva")
Username (ex: "joao.silva" ou "joao123")

Único dentro do estabelecimento
Usado para fazer login
Não precisa ser email


Senha

Hash armazenado no banco
Definida no momento da criação


Flag is_admin (true/false)
Status ativo/inativo

4. Sistema de Permissões Granulares
Recursos do Sistema
Lista de recursos que podem ter permissões:

Comandas
Mesas
Cardápio
Estoque
Fornecedores
Relatórios
Financeiro
Caixa
Usuários
Configurações

Tipos de Permissão por Recurso
Para cada recurso, um usuário pode ter:

Visualizar (ver informações)
Criar (adicionar novos registros)
Editar (modificar existentes)
Excluir (remover registros)

Exemplo Prático
Um garçom poderia ter:

Comandas: visualizar ✓, criar ✓, editar ✓, excluir ✗
Mesas: visualizar ✓, criar ✗, editar ✗, excluir ✗
Cardápio: visualizar ✓, criar ✗, editar ✗, excluir ✗
Estoque: visualizar ✗, criar ✗, editar ✗, excluir ✗
Relatórios: visualizar ✗, criar ✗, editar ✗, excluir ✗

Um caixa poderia ter:

Comandas: visualizar ✓, criar ✗, editar ✓, excluir ✗
Caixa: visualizar ✓, criar ✓, editar ✓, excluir ✗
Financeiro: visualizar ✓, criar ✗, editar ✗, excluir ✗

5. Fluxo de Criação
Primeiro Acesso (Cadastro do Restaurante)

Dono preenche dados do restaurante
Define seu username e senha
Esse usuário é marcado como is_admin = true
Recebe automaticamente todas as permissões

Criação de Funcionários (pelo Admin)

Admin acessa área de "Usuários"
Clica em "Novo Usuário"
Preenche:

Nome completo
Username
Senha inicial


Seleciona permissões:

Lista todos os recursos
Para cada recurso, marca quais ações o usuário pode fazer


Salva
Usuário já pode fazer login

6. Tela de Login
Interface simples:

Campo "Usuário" (username)
Campo "Senha"
Botão "Entrar"
Opção "Esqueci minha senha" (admin pode resetar)

7. Validações de Segurança
No Login:

Username deve existir no estabelecimento
Senha deve corresponder ao hash
Usuário deve estar ativo
Criar sessão/token JWT após validação

No Sistema:

Toda ação verifica se usuário tem permissão
Admin sempre passa em todas as verificações
Usuário comum precisa ter a permissão específica
Exemplo: ao tentar excluir uma comanda, verificar se pode_excluir em comandas é true

8. Gestão de Permissões pelo Admin
Tela de Edição de Usuário:

Admin pode ver lista de todos os usuários
Ao clicar em um usuário, vê:

Dados cadastrais (nome, username)
Tabela de permissões (recursos x ações)
Checkboxes para marcar/desmarcar permissões


Pode ativar/desativar usuário
Pode resetar senha
Pode excluir usuário
Não pode editar o próprio status de admin ou remover suas permissões

9. Log de Auditoria
Registrar em log:

Quem fez login (username, data/hora)
Quem criou/editou/excluiu comandas
Quem deu descontos
Quem fechou caixas
Quem modificou estoque
Quem criou/editou/excluir usuários
Quem alterou permissões

Isso permite rastreabilidade completa das ações.
10. Regras Importantes

Username é único por estabelecimento (dois restaurantes podem ter "admin", mas não dentro do mesmo)
Admin não pode remover seu próprio acesso
Sempre deve existir pelo menos um admin ativo no estabelecimento
Permissões são aditivas (usuário só pode fazer o que foi explicitamente permitido)
Admin tem todas as permissões automaticamente, não precisa cadastrar uma por uma

11. Estrutura de Dados Resumida
Tabela usuarios:

id
estabelecimento_id
nome
username
senha_hash
is_admin (boolean)
ativo (boolean)
created_at

Tabela permissoes:

id
usuario_id
recurso (ex: "comandas", "estoque")
pode_visualizar (boolean)
pode_criar (boolean)
pode_editar (boolean)
pode_excluir (boolean)

Tabela audit_log:

id
usuario_id
acao (descrição do que foi feito)
recurso (onde foi feito)
detalhes (JSON com dados adicionais)
timestamp
# Changelog

Todas mudanças notáveis deste projeto documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Categorias: `Added`, `Changed`, `Fixed`, `Removed`, `Security`.

## [Unreleased]

<!-- Novas entradas entram aqui, no topo. Ver CLAUDE.md → "Changelog" para o padrão de preenchimento. -->

### Fixed

- Corrige anotações `Mapped[X | None]` incompatíveis com Python 3.9 em src/models — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20

### Removed

- Remove funcionalidade de backup (rota, serviço e aba na UI) — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20

### Security

- Bloqueia auto-escalação de permissões — usuário não pode mais alterar as próprias telas de acesso — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Corrige endpoint check-email que expunha existência de e-mails de qualquer tenant sem exigir permissão — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20
- Elimina vetor de vazamento de dados de todos os tenants (senha, tokens) via rota de backup que ignorava RLS — Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>, 2026-08-20

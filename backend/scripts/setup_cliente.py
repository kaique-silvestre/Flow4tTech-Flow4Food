"""
Provisiona um novo banco de dados para um cliente.

Uso:
    python scripts/setup_cliente.py \
        --db matchpoint_matheus \
        --username teste_matheus \
        --password MatheusTeste1234 \
        --name "Matheus" \
        --empresa "MatchpointTeste"

O script:
  1. Cria o banco Postgres (se não existir)
  2. Roda todas as migrations (alembic upgrade head)
  3. Cria o usuário como Admin com acesso a todas as telas
"""

import argparse
import os
import subprocess
import sys
from urllib.parse import urlparse, urlunparse

import bcrypt
import sqlalchemy as sa


def _parse_base_url(database_url: str) -> tuple[str, str]:
    """Retorna (url_sem_banco, nome_do_banco_atual)."""
    p = urlparse(database_url)
    db_name = p.path.lstrip("/")
    admin_url = urlunparse(p._replace(path="/postgres"))
    return admin_url, db_name


def criar_banco(database_url: str, novo_banco: str) -> None:
    admin_url, _ = _parse_base_url(database_url)
    engine = sa.create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            sa.text("SELECT 1 FROM pg_database WHERE datname = :db"),
            {"db": novo_banco},
        ).fetchone()
        if exists:
            print(f"[info] Banco '{novo_banco}' já existe — pulando criação.")
        else:
            conn.execute(sa.text(f'CREATE DATABASE "{novo_banco}"'))
            print(f"[ok] Banco '{novo_banco}' criado.")
    engine.dispose()


def rodar_migrations(nova_url: str) -> None:
    print("[info] Rodando alembic upgrade head...")
    env = {**os.environ, "DATABASE_URL": nova_url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if result.returncode != 0:
        print("[erro] Migrations falharam.")
        sys.exit(1)
    print("[ok] Migrations aplicadas.")


def criar_usuario(nova_url: str, username: str, password: str, name: str) -> None:
    engine = sa.create_engine(nova_url)
    with engine.begin() as conn:
        admin_profile = conn.execute(
            sa.text("SELECT id FROM profiles WHERE tenant_id = 1 AND name = 'Admin'")
        ).fetchone()
        if admin_profile is None:
            print("[erro] Perfil Admin não encontrado. Verifique se as migrations rodaram.")
            sys.exit(1)

        exists = conn.execute(
            sa.text("SELECT id FROM system_users WHERE username = :u"),
            {"u": username},
        ).fetchone()
        if exists:
            print(f"[info] Usuário '{username}' já existe — pulando criação.")
        else:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                sa.text(
                    "INSERT INTO system_users "
                    "(tenant_id, profile_id, name, username, email, password_hash, is_active) "
                    "VALUES (1, :pid, :name, :username, NULL, :phash, true)"
                ),
                {
                    "pid": admin_profile[0],
                    "name": name,
                    "username": username,
                    "phash": password_hash,
                },
            )
            print(f"[ok] Usuário '{username}' criado com perfil Admin.")
    engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Provisiona cliente Matchpoint")
    parser.add_argument("--db", required=True, help="Nome do banco Postgres a criar")
    parser.add_argument("--username", required=True, help="Login do usuário admin do cliente")
    parser.add_argument("--password", required=True, help="Senha do usuário")
    parser.add_argument("--name", required=True, help="Nome completo do usuário")
    parser.add_argument("--empresa", default="", help="Nome da empresa (informativo)")
    args = parser.parse_args()

    base_url = os.environ.get("DATABASE_URL", "")
    if not base_url:
        print("[erro] Variável DATABASE_URL não definida. Ative o venv e defina a variável.")
        sys.exit(1)

    p = urlparse(base_url)
    nova_url = urlunparse(p._replace(path=f"/{args.db}"))

    print(f"\n=== Provisionando cliente: {args.empresa or args.db} ===")
    print(f"  Banco:    {args.db}")
    print(f"  Usuário:  {args.username}")
    print(f"  URL:      {nova_url}\n")

    criar_banco(base_url, args.db)
    rodar_migrations(nova_url)
    criar_usuario(nova_url, args.username, args.password, args.name)

    print(f"""
=== Concluído ===
  Login:  {args.username}
  Banco:  {args.db}

Para rodar o backend apontando para esse cliente:
  $env:DATABASE_URL="{nova_url}"
  uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
""")


if __name__ == "__main__":
    main()

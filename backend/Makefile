.PHONY: install dev lint format type-check test migrate makemigration

install:
	pip install -e ".[dev]"

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy src

test:
	pytest -q

migrate:
	alembic upgrade head

makemigration:
	alembic revision --autogenerate -m "$(name)"

check: lint type-check test

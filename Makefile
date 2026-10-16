.PHONY: install migrate seed api web test lint build
install:
	pnpm install --frozen-lockfile
	cd apps/api && uv sync --frozen
migrate:
	cd apps/api && uv run alembic upgrade head
seed:
	cd apps/api && uv run python -m oriade.cli seed
api:
	cd apps/api && uv run uvicorn oriade.main:app --reload --host 127.0.0.1 --port 8000
web:
	pnpm dev
test:
	cd apps/api && uv run pytest -q
	pnpm test
lint:
	cd apps/api && uv run ruff check src tests && uv run ruff format --check src tests migrations
	pnpm lint
	pnpm typecheck
build:
	pnpm build

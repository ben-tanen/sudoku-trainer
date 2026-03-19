.PHONY: run install

install:
	uv sync

run:
	op run --env-file=.env -- uv run uvicorn app.main:app --reload --port 8000

#!/bin/bash
set -e

uv sync --extra dev

if [[ "$1" == "ci" ]]; then
  uv run ruff check ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
  uv run ruff format --check ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
else
  uv run ruff check --fix ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
  uv run ruff format ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
fi
uv run mypy ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py

if [[ "$1" == "ci" ]]; then
  uv run pytest --cov=main --cov=app --cov-branch --cov-report=term --cov-report=xml
else
  uv run pytest --cov=main --cov=app --cov-branch --cov-report=term
fi

# Check GitHub Actions workflows for security issues
if [[ "$1" == "ci" ]]; then
  uv run zizmor .github/workflows/
else
  uv run zizmor --fix .github/workflows/
fi

#!/bin/bash
set -e

uv sync --extra dev

if [[ "$1" == "ci" ]]; then
  uv run black --check ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
else
  uv run black ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
fi

uv run flake8 ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
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

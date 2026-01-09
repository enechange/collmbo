#!/bin/bash
set -e

uv sync --extra dev

if [[ -n "$CI" ]]; then
  uv run ruff check
  uv run ruff format --check
  uv run ty check
  uv run pytest --cov --cov-report=term --cov-report=xml
else
  uv run ruff check --fix
  uv run ruff format
  uv run ty check
  uv run pytest --cov --cov-report=term
fi

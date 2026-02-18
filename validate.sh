#!/bin/bash
set -e

mise install
uv sync --extra dev

if [[ -n "$CI" ]]; then
  uv run pip-licenses --partial-match --allow-only="Apache;BSD;CNRI-Python;ISC;MIT;MPL;PSF;Python Software Foundation"
  ruff check
  ruff format --check
  ty check
  uv run pytest --cov --cov-report=term --cov-report=xml
else
  uv run pip-licenses --summary
  ruff check --fix
  ruff format
  ty check
  uv run pytest --cov --cov-report=term
fi

hadolint Dockerfile

actionlint
ghalint run
if [[ -n "$CI" ]]; then
  zizmor .github/workflows/
  pinact run --check
else
  zizmor --fix .github/workflows/
  pinact run
fi

#!/bin/bash
set -e

uv pip install --system -r pyproject.toml --extra dev

if [[ "$1" == "ci" ]]; then
  black --check ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
else
  black ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
fi

flake8 ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py
mypy ./*.py ./app/*.py ./app/mcp/*.py ./tests/*.py ./tests/mcp/*.py

if [[ "$1" == "ci" ]]; then
  pytest --cov=main --cov=app --cov-branch --cov-report=term --cov-report=xml
else
  pytest --cov=main --cov=app --cov-branch --cov-report=term
fi

# Check GitHub Actions workflows for security issues
if [[ "$1" == "ci" ]]; then
  zizmor .github/workflows/
else
  zizmor --fix .github/workflows/
fi

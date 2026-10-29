.DEFAULT_GOAL := help
.PHONY: help install lint format test check run eval-build eval-validate eval build deploy

CSV ?= data/sample.csv
DATASET ?= seed-v1

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

install: ## Install locked dependencies and the git hooks
	uv sync --locked
	uv run pre-commit install

lint: ## Ruff lint + format check, mypy --strict
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

format: ## Apply ruff fixes and formatting
	uv run ruff check --fix .
	uv run ruff format .

test: ## Unit tests with the coverage gate
	uv run pytest --cov --cov-report=term-missing

check: lint test ## Everything CI runs

run: ## Classify a CSV locally with real Bedrock calls (CSV=path, default data/sample.csv)
	uv run triagelite run $(CSV)

eval-build: ## Freeze reviewed candidates into evals/datasets/$(DATASET) (once, never rebuilt)
	uv run python -m evals.build $(DATASET)

eval-validate: ## Check a frozen dataset: hashes, counts, cells, groups, labels
	uv run python -m evals.validate $(DATASET)

eval: ## Run the eval harness
	@echo "eval: not implemented yet" >&2; exit 1

build: ## Build Lambda packages
	@echo "build: not implemented yet" >&2; exit 1

deploy: ## Deploy with Terraform
	@echo "deploy: not implemented yet" >&2; exit 1

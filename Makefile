.DEFAULT_GOAL := help
.PHONY: help install lint format test check run eval-build eval-validate eval eval-compare eval-similarity eval-dedupe build deploy

CSV ?= data/sample.csv
DATASET ?= seed-v1
PROMPT ?= classify/v1
REPEAT ?= 1
CHUNK ?=
MODEL ?=
API ?=

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-15s %s\n", $$1, $$2}'

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

eval: ## Run the eval harness on the tuning split (PROMPT=classify/v1, REPEAT=1, CHUNK/MODEL/API=config)
	uv run python -m evals.harness --dataset $(DATASET) --split tuning --prompt $(PROMPT) --repeat $(REPEAT) $(if $(CHUNK),--chunk-size $(CHUNK)) $(if $(MODEL),--model $(MODEL)) $(if $(API),--api $(API))

eval-compare: ## Paired bootstrap of two harness results (BASE=json CANDIDATE=json)
	uv run python -m evals.compare $(BASE) $(CANDIDATE)

eval-similarity: ## Embed the tuning split and sweep dedupe thresholds (plot + table)
	uv run python -m evals.similarity --dataset $(DATASET)

eval-dedupe: ## Dedupe precision/recall on the tuning split, with and without the judge
	uv run python -m evals.dedupe --dataset $(DATASET) --split tuning

build: ## Build Lambda packages
	@echo "build: not implemented yet" >&2; exit 1

deploy: ## Deploy with Terraform
	@echo "deploy: not implemented yet" >&2; exit 1

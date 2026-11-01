.PHONY: help sync test lint format check install gifs clean

help: ## Show this help
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-10s %s\n", $$1, $$2}'

sync: ## Install project and dev dependencies
	uv sync

test: ## Run the tests
	uv run pytest

lint: ## Check lint and formatting (what CI runs)
	uv run ruff check .
	uv run ruff format --check .

format: ## Auto-fix lint issues and format the code
	uv run ruff check --fix .
	uv run ruff format .

check: lint test ## Lint and test, run before committing

install: ## Install the `iring` command on your PATH (editable)
	uv tool install --editable --reinstall .

gifs: ## Re-record the README GIFs (needs vhs and a connected iPhone)
	cd docs && vhs demo.tape && vhs delete.tape

clean: ## Remove caches
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -not -path "./.venv/*" -exec rm -rf {} +

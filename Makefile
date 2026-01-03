.DEFAULT: help

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: setup
setup: ## Setup the development environment
	@uv venv -p $$(asdf which python) --clear
	@uv sync --all-extras
	@git lfs install

.PHONY: check
check: ## Checks formatting, linting and type errors.
	@uv run ruff format .
	@uv run ruff check --fix .
	@uv run mypy .

.PHONY: test
test: ## Run tests.
	@uv run pytest

.PHONY: test-in-ci
test-in-ci: ## Run tests and generate coverage report for CI.
	@rm -rf .coverage
	@rm -rf coverage
	@mkdir -p coverage
	@uv run pytest --cov=. --cov-report=xml:coverage/cobertura-coverage.xml
	@echo "Coverage report generated in coverage/cobertura-coverage.xml"

.PHONY: install-dev
install-dev:	## Install the project in editable mode.
	@uv pip install -e .

.PHONY: sim
sim: ## Run in simulation mode using Mujoco
	@uv run mjpython -m reachy_mini.daemon.app.main --sim

.PHONY: clean
clean: ## Clean up temporary files and directories.
	@rm -rf .coverage
	@rm -rf coverage
	@find . -type d -name "__pycache__" -exec rm -r {} +
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf .venv
	@rm -rf .ruff_cache

.PHONY: update-version
update-version: ## Bump version in pyproject.toml.
	@LATEST_TAG=$$(git describe --tags --abbrev=0 | sed 's/^v//') && \
	echo "Updating version to $$LATEST_TAG" && \
	sed -i '' "s/^version = \".*\"/version = \"$$LATEST_TAG\"/" pyproject.toml

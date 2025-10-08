SOURCES = ./pybsn/ ./bin/ ./examples/ ./test/
FLAKE8_SOURCES = ./pybsn/ ./bin/* ./examples/*.py ./test/*.py

.PHONY: fast-lint
fast-lint:
	uv run ruff check $(SOURCES)
	uv run isort --check $(SOURCES)
	uv run black --check $(SOURCES)

.PHONY: lint
lint: fast-lint

.PHONY: check
check:
	uv run mypy pybsn

.PHONY: fix
fix:
	uv run ruff check --fix $(SOURCES)
	uv run isort $(SOURCES)
	uv run black $(SOURCES)

.PHONY: coverage
coverage:
	uv run coverage run --omit */*-packages/* -m unittest discover -v

.PHONY: coverage-report
coverage-report:
	uv run coverage report

.PHONY: install-deps
install-deps:
	uv sync --all-extras

.PHONY: sync
sync:
	uv sync --all-extras

.PHONY: reformat
reformat:
	uv run black $(SOURCES)

.PHONY: test
test:
	uv run --with .[test] python -m unittest discover -v

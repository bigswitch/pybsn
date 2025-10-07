SOURCES = ./pybsn/ ./bin/ ./examples/ ./test/
FLAKE8_SOURCES = ./pybsn/ ./bin/* ./examples/*.py ./test/*.py

.PHONY: fast-lint
fast-lint:
	uv run flake8 $(FLAKE8_SOURCES) --count --max-complexity=20 --max-line-length=127 --show-source --statistics
	# validation will be enabled after reformatting
	# uv run black --check $(SOURCES)

.PHONY: check
check: fast-lint

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

.PHONY: check
check:
	uv run flake8 ./pybsn/ ./bin/* ./examples/*.py ./test/*.py --count --max-complexity=20 --max-line-length=127 --show-source --statistics

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

.PHONY: test
test:
	uv run --with .[test] python -m unittest discover -v

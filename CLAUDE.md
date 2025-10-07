# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

pybsn is a Python interface to Arista Networks BigDB/Atlas based products (formerly Big Switch Networks). It provides both a low-level REST API client (`BigDbClient`) and a high-level Node abstraction for interacting with the BigDB REST API.

## Core Architecture

### Main Components

**BigDbClient** (`pybsn/__init__.py`):
- Low-level API client exposing HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Handles authentication via username/password (interactive session) or API tokens
- Entry point via `pybsn.connect(host, username=None, password=None, token=None, verify_tls=False)`

**Node Abstraction** (`pybsn/__init__.py`):
- High-level dynamic tree navigation interface accessed via `client.root`
- Hyphens in REST API paths are converted to underscores for Python (e.g., `root.core.switch_config` → `controller/core/switch-config`)
- Supports chaining with predicates: `root.core.switch_config.match(name='sn1')()`
- Python keywords accessed via dictionary notation: `root.os.config["global"]`

**Data format**: Dictionary keys in data passed to the API must use BigDB schema format (hyphens, not underscores): `{"mac-address": "01:02:03:04:05:06"}`

### Key Files

- `pybsn/__init__.py` - Single-file implementation containing all client code
- `bin/pybsn-repl` - Interactive IPython shell for API exploration
- `bin/pybsn-schema` - Schema inspection tool
- `test/` - Unit tests using `responses` library for mocking
- `examples/` - Usage examples for various BigDB operations

## Development Commands

### Install Dependencies
```bash
make install-deps
# Or for development in pipenv/venv:
python -m pip install --upgrade pip
python -m pip install coverage flake8
python -m pip install -r requirements.txt
```

### Running Tests
```bash
# Run all tests
python -m unittest discover

# Run specific test
python -m unittest test.test_bigdb_client.TestBigDBClient.test_connect_modern_login

# Run with coverage
make coverage
make coverage-report
```

### Code Quality
```bash
# Lint (flake8 with max-line-length=127, max-complexity=20)
make check
```

### Running pybsn-repl Locally
```bash
# From source without installing
PYTHONPATH=. ./bin/pybsn-repl -H <controller_host> -u <user> -p <passwd>
```

## Testing Notes

- Tests use the `responses` library to mock HTTP requests
- Test utilities in `test/fakeserver.py` and `test/mockutils.py`
- No integration tests requiring actual BigDB instance in standard test suite
- Coverage reporting excludes site-packages: `coverage run --omit */*-packages/* -m unittest discover -v`

## Release Process

Releases are automated via GitHub Actions when tags are pushed:
- Version defined in `setup.py`
- Tag push triggers both GitHub release and PyPI upload
- Main branch is `main` (not `master`)

## Python Version Support

- Supports Python 3.8+
- CI runs on ubuntu-22.04 and ubuntu-latest
- Uses `setuptools` with legacy build backend (see `pyproject.toml`)

## Common Patterns

### Authentication
```python
# Recommended: Use API token
client = pybsn.connect(host=host, token="<token>", verify_tls=True)

# Alternative: Username/password (creates interactive session)
client = pybsn.connect(host=host, username="<user>", password="<password>")
```

### Node Operations
```python
# GET request
switches = root.core.switch()

# With predicate
switch = root.core.switch.match(name="leaf-1a")()

# POST/PUT/PATCH with data (note: keys use hyphens)
root.core.switch_config.post({"name": "leaf-1a", "mac-address": "01:02:03:04:05:06"})

# RPC call
root.core.switch.match(name="leaf-1a").disconnect.rpc()

# Schema inspection (append # in repl)
root.core.switch#
```

## Bugtracking
The system uses Arista's internal Bugtracking system (Bugsby). The package is `pybsn`. Omit --component. There are no bugsby components in this package.

## Workflow
Always create a bug for each independent unit of work.
Create a branch named `bug<bug-id>-<short-memo>` for each change.
Create pull requests with a title of `BUG<bug-id> <title>'
ALWAYS include `Fixes: BUG<bug-id>` at the bottom of the PR description. Separate from other content in the description with an empty line, following
git commit trailer semantics. If you include a Claude attribution, make sure the `Fixes` trailer is still at the very bottom of the description.

## Barney Build System

The project uses Barney (internal build system) with configuration in `barney.yaml`. The package image copies `pybsn/__init__.py` to `/dest/pybsn/`.

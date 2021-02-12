check: check-line-length check-syntax

check-line-length:
	flake8 ./pybsn/ ./bin/* --count --max-complexity=20 --max-line-length=127 --statistics

check-syntax:
	flake8 ./pybsn/ ./bin/* --count --select=E9,F63,F7,F82 --show-source --statistics

coverage:
	coverage run --omit */*-packages/* -m unittest discover -v

coverage-report:
	coverage report

install-deps:
	# for development, consider running in a pipenv/venv
	python -m pip install --upgrade pip
	python -m pip install coverage flake8
	python -m pip install -r requirements.txt

.PHONY: debian lint install
debian:
	fakeroot debian/rules clean build binary
install:
	python3 setup.py install
lint:
	# Duplicate code detected in imports
	# - https://github.com/PyCQA/pylint/issues/803
	#   > Wouldn't that disable all kinds of import linting?
	#   > Nope, only similarities with regard imports.
	pylint3 flos3 \
		--ignore-imports=yes


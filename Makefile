# Copyright (c) 2024 Joel Torres
# Distributed under the MIT software license, see the accompanying
# file LICENSE or https://opensource.org/license/mit.

PY = python3
VENV_DIR = .venv
VENV_EXEC = $(VENV_DIR)/bin/activate

test: clean
	. $(VENV_EXEC) && $(PY) -m pytest -v .

build: test
	$(PY) -m build

push: build
	. $(VENV_EXEC) && $(PY) -m twine upload dist/*

clean:
	rm -rf dist
	rm -rf *egg*
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf tmp

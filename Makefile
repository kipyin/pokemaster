SHELL: /bin/bash

.ONESHELL:
.PHONY: install
install:
	@curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
	@source $$HOME/.poetry/env
	@poetry install -v


.PHONY: test-html
test-html:
	@poetry run pytest --cov=pokemaster --cov-report=html tests/

.PHONY: test
test:
	@poetry run pytest --cov=pokemaster tests/

.PHONY: format
format:
	@isort -rc .
	@black .


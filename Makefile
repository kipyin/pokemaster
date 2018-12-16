.PHONY: test
test:
	@poetry run pytest -v --cov=pokemaster tests/

.PHONY: test-pdb
test-pdb:
	@poetry run pytest -v --pdb --cov=pokemaster tests/

.PHONY: format
format:
	@isort -rc .
	@black .


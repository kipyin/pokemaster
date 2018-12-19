.PHONY: test
test:
	@poetry run pytest -q --cov=pokemaster tests/

.PHONY: test-pdb
test-pdb:
	@poetry run pytest -q --pdb tests/

.PHONY: test-ff
test-ff:
	@poetry run pytest -qx --ff tests/

.PHONY: format
format:
	@isort -rc .
	@black .


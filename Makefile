.PHONY: test
test:
	@poetry run pytest -v --cov=pokemaster tests/

.PHONY: format
format:
	@isort -rc .
	@black .


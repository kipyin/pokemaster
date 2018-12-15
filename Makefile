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


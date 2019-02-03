.PHONY: test
test:
	@poetry run pytest -q --cov=pokemaster --no-cov-on-fail tests/

.PHONY: test-html
test-html:
	@poetry run pytest -q --cov=pokemaster --cov-report=html --no-cov-on-fail tests/
	@open htmlcov/index.html

.PHONY: format
format:
	@isort -rc .
	@black .


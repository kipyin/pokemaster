"""
Provides short-hand commands to aid testing and developing.
"""

from invoke import task


@task
def lint(c):
    """Lint the codes."""
    c.run('isort -rc .')
    c.run('black .')


@task(iterable=['tests'])
def test(c, tests=None, report=False):
    """Run tests.

    :param tests: The tests to run. This is a list of test file names
        without the 'tests/' prefix. If no tests are given, all tests
        will be run.
    :param report: Generate the coverage report in HTML.
    :return: NoReturn
    """
    if not tests:
        tests_to_run = ['tests/']
    else:
        tests_to_run = list(map(lambda x: 'tests/' + x, tests))

    c.run(
        f'poetry run pytest '
        f'-q --cov=pokemaster '
        f'{"--cov-report=html" if report else ""} '
        f'{" ".join(tests_to_run)}'
    )
    if report:
        c.run('open htmlcov/index.html')

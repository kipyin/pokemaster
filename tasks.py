from invoke import task


@task
def format(c):
    c.run('isort -rc .')
    c.run('black .')


@task(iterable=['tests'])
def test(c, tests):
    if not tests:
        tests = ['tests/test_pokemon.py']
    elif tests == 'all':
        tests = ['tests/']
    c.run(f'poetry run pytest -qx --ff {" ".join(tests)}')

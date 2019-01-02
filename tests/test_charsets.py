import pytest

from pokemaster.charset import Charset

# from hypothesis import given
# from hypothesis.strategies import characters


def test_charset_sanity():
    assert Charset('Pokemon')


def test_charset_raise_error_for_invalid_chars():
    with pytest.raises(ValueError):
        Charset('Pokémon')


def test_charset_encode():
    assert Charset('Pokemon').encode() == b'\xe2\xe3\xe1\xd9\xdf\xe3\xca'


def test_charset_decode():
    assert Charset.decode(b'\xe2\xe3\xe1\xd9\xdf\xe3\xca') == 'Pokemon'


def test_charset_encode_decode_sanity():
    assert Charset.decode(Charset('Pokemon').encode()) == 'Pokemon'

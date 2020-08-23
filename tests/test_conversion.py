import pytest

from un_fstring import convert_f_strings_to_strings_format


@pytest.mark.parametrize(
    "input, expected",
    [
        ('f"{foobar}"', '"{}".format(foobar)'),
        ('f"hello {a} goodbye {b}"', '"hello {} goodbye {}".format(a, b)'),
    ],
)
def test_conversion(input, expected):
    assert convert_f_strings_to_strings_format(input) == expected

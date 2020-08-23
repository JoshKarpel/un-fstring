import pytest

from un_fstring import convert_f_strings_to_strings_format


@pytest.mark.parametrize(
    "input, expected",
    [
        ('f"{foobar}"', "'{}'.format(foobar)"),
        ('f"{foobar!a}"', "'{!a}'.format(foobar)"),
        ('f"{foobar:20}"', "'{:20}'.format(foobar)"),
        ('f"{foobar!a:20}"', "'{!a:20}'.format(foobar)"),
        ('f"{math.sin(20)}"', "'{}'.format(math.sin(20))"),
        ('f"{[x for x in range(1)]}"', "'{}'.format([x for x in range(1)])"),
        ('f"hello {a} goodbye {b}"', "'hello {} goodbye {}'.format(a, b)"),
        ('f"hello {a!r:20} goodbye {b!a}"', "'hello {!r:20} goodbye {!a}'.format(a, b)"),
    ],
)
def test_conversion(input, expected):
    assert convert_f_strings_to_strings_format(input) == expected

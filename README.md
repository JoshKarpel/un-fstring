# un-fstring

![PyPI](https://img.shields.io/pypi/v/un-fstring)

![tests](https://github.com/JoshKarpel/un-fstring/workflows/tests/badge.svg)
![PyPI - License](https://img.shields.io/pypi/l/un-fstring)

Sometimes, unfortunately, you need to write code that is compatible with Python 3.5
(e.g., to run on Ubuntu 16 or Debian 9, which will be supported
until April 2021 and June 2022, respectively).
Sometimes, even more unfortunately, you didn't know it needed to be when you
wrote it, and you need to make it compatible post-facto.
The biggest syntax changes going from 3.5 to 3.6 was the addition of
[f-strings](https://docs.python.org/3/whatsnew/3.6.html#pep-498-formatted-string-literals),
and [many](https://github.com/asottile/pyupgrade)
[packages](https://github.com/ikamensh/flynt)
can convert old-style string formatting methods into f-strings.
`un-fstring` does the opposite: it converts f-strings into `.format()` calls
to preserve compatibility with Python 3.5.

To convert your code, first install `un-fstring` (it itself requires Python 3.6 or later):
```console
$ pip install un-fstring
```
Then run it over your source code:
```console
$ un-fstring path/to/source/directory another_file.py
```
`un-fstring` will replace f-strings with `.format()` calls in-place.

The `--dry-run` option will show a contextual diff
of what `un-fstring` would do to your code without actually overwriting it.
Run `un-fstring --help` to see what other options are available.

`un-fstring` is not a code formatter;
I recommend running
[`black`](https://github.com/psf/black)
over your code afterwards with the `--target-version py35` option enabled.

> Though potentially useful, this is mostly a toy project based on some problems
> I ran into at work.
> If you're looking for a more robust implementation, check out
> [f2format](https://github.com/pybpc/f2format).

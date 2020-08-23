#!/usr/bin/env python3

import argparse
import ast
import difflib
import os
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional

import astroid
from tokenize_rt import Offset, Token, src_to_tokens, tokens_to_src

WINDOWS = os.name == "nt"


class FindFStrings(ast.NodeVisitor):
    def __init__(self) -> None:
        self.fstrings: Dict[Offset, ast.JoinedStr] = {}

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        offset = Offset(node.lineno, node.col_offset)
        self.fstrings[offset] = node

        self.generic_visit(node)


def convert_f_strings_to_strings_format(src: str) -> str:
    """
    Convert all f-string in arbitrary source code to .format() calls,
    returning the full modified source code.
    """
    ast_ = ast.parse(src)

    visitor = FindFStrings()
    visitor.visit(ast_)

    tokens = src_to_tokens(src)

    for idx, token in enumerate(tokens):
        if token.offset in visitor.fstrings and token.src.startswith("f"):
            tokens[idx] = Token(
                name=token.name,
                src=convert_f_string_to_format_string(token.src),
                line=token.line,
                utf8_byte_offset=token.utf8_byte_offset,
            )

    return tokens_to_src(tokens)


CONVERSIONS = {-1: "", 115: "!s", 114: "!r", 97: "!a"}


def convert_f_string_to_format_string(src: str) -> str:
    """
    Convert a single f-string (passed as its source token)
    to a .format() call (as a source token).
    """
    node = astroid.extract_node(src)

    # An f-string alternates between two kinds of nodes: string Const nodes and
    # FormattedValue nodes that hold the formatting bits
    format_string_parts = []
    format_args = []
    for child in node.get_children():
        if isinstance(child, astroid.Const):
            format_string_parts.append(child.value)
        elif isinstance(child, astroid.FormattedValue):
            format_string_parts.append(
                "{{{c}{f}}}".format(
                    c=CONVERSIONS[child.conversion],
                    f=f":{child.format_spec.values[0].value}"
                    if child.format_spec is not None
                    else "",
                )
            )

            # We can pick the format value nodes right out of the string
            # and place them in the args; no need to introspect what they
            # actually are!
            format_args.append(child.value)

    format_string_node = astroid.Const("".join(format_string_parts))

    format_call = astroid.Call(lineno=node.lineno, col_offset=node.col_offset)

    # The Call's func is a method looked up on the format string
    format_attr = astroid.Attribute(attrname="format", lineno=node.lineno, parent=format_call)
    format_attr.postinit(expr=format_string_node)

    # The Call's arguments are the format arguments extracted from the f-string
    format_call.postinit(func=format_attr, args=format_args, keywords=[])

    return format_call.as_string()


def convert_file(file: Path, conversions: List[Callable[[str], str]], dry_run: bool) -> bool:
    """
    Run a list of conversions over a file.
    Each conversion takes in the file contents
    (possibly modified by a prior conversion)
    and emits a new version of the file contents.

    Parameters
    ----------
    file
        The file to convert.
    conversions
        The conversions to run.
    dry_run
        If ``False``, and the final file contents do not match the original,
        the file will be overwritten with the converted contents.
        If ``True``, instead print a diff showing how the file would change.

    Returns
    -------
    was_modified : bool
        ``True`` if the file was/would be modified.
    """
    mod = src = file.read_text()

    for conversion in conversions:
        mod = conversion(src)

    was_modified = src != mod

    if was_modified and not dry_run:
        # Atomic overwrite on Linux
        if WINDOWS:
            file.write_text(mod)
        else:
            tmp_file = file.with_name(file.name + ".tmp")
            tmp_file.write_text(mod)
            tmp_file.rename(file)

        print(f"Modified {file}")
    elif was_modified and dry_run:
        print(diff(src, mod, file))

    return was_modified


def diff(a: str, b: str, path: Path) -> str:
    return "".join(
        difflib.unified_diff(
            a.splitlines(keepends=True),
            b.splitlines(keepends=True),
            fromfile=str(path),
            tofile=f"un-fstring({path})",
        )
    )


def gather_files(paths: Iterable[Path]) -> Iterator[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from gather_files(path.iterdir())


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Down-convert f-strings to .format() calls for compatibility with Python <3.6"
    )

    parser.add_argument(
        "path",
        nargs="*",
        type=Path,
        help="paths to files (or directories of files, searched recursively) to down-convert f-strings in",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="if passed, do not overwrite files, and show a diff of what would be written instead",
    )

    return parser.parse_args(args)


def cli() -> int:
    args = parse_args()

    files = list(gather_files(args.path))

    modified = [
        convert_file(
            file=file, conversions=[convert_f_strings_to_strings_format], dry_run=args.dry_run
        )
        for file in files
    ]

    if any(modified):
        if args.dry_run:
            print(
                f"Checked {len(files)} files; would have modified {sum(modified)} file{'s' if sum(modified) > 1 else ''}"
            )
        else:
            print(
                f"Checked {len(files)} files; modified {sum(modified)} file{'s' if sum(modified) > 1 else ''}"
            )
        return 1
    else:
        print(f"Checked {len(files)} files; didn't have to do anything!")
        return 0


if __name__ == "__main__":
    sys.exit(cli())

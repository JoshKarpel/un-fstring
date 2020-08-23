#!/usr/bin/env python3

import argparse
import ast
import difflib
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple, cast

from tokenize_rt import Offset, Token, src_to_tokens, tokens_to_src


class FindFStrings(ast.NodeVisitor):
    def __init__(self) -> None:
        self.fstrings: Dict[Offset, ast.JoinedStr] = {}

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        offset = Offset(node.lineno, node.col_offset)
        self.fstrings[offset] = node

        self.generic_visit(node)


def convert_f_strings_to_strings_format(src: str) -> str:
    ast_ = ast.parse(src)

    visitor = FindFStrings()
    visitor.visit(ast_)

    tokens = src_to_tokens(src)

    for idx, token in enumerate(tokens):
        if token.offset in visitor.fstrings and token.src.startswith("f"):
            s, args = parse_f_string(visitor.fstrings[token.offset])
            tokens[idx] = Token(
                name=token.name,
                src='"{}".format({})'.format(s, ", ".join(args)),
                line=token.line,
                utf8_byte_offset=token.utf8_byte_offset,
            )

    return tokens_to_src(tokens)


def parse_f_string(node: ast.JoinedStr) -> Tuple[str, List[str]]:
    s = []
    args = []

    for part in node.values:
        if isinstance(part, ast.Str):
            s.append(part.value)
        elif isinstance(part, ast.FormattedValue):
            s.append("{}")

            # the value of the FormattedValue node is always a Name
            name = cast(ast.Name, part.value)
            args.append(name.id)

    return "".join(s), args


def fix_file(file: Path, conversions: List[Callable[[str], str]], dry_run: bool) -> bool:
    mod = src = file.read_text()

    for conversion in conversions:
        mod = conversion(src)

    was_modified = src != mod

    if was_modified and not dry_run:
        file.write_text(mod)
        print("Modified {}".format(file))
        print(diff(src, mod, file))
    elif was_modified and dry_run:
        print(diff(src, mod, file))

    return was_modified


def diff(a: str, b: str, path: Path) -> str:
    return "".join(
        difflib.unified_diff(
            a.splitlines(keepends=True),
            b.splitlines(keepends=True),
            fromfile=str(path),
            tofile="un_fstring({})".format(path),
        )
    )


def gather_files(paths: Iterable[Path]) -> Iterator[Path]:
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from gather_files(path.iterdir())


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("path", nargs="*", type=Path)
    parser.add_argument("--dry-run", "-d", action="store_true")

    return parser.parse_args(args)


def cli() -> int:
    args = parse_args()

    files = list(gather_files(args.path))

    modified = [
        fix_file(file=file, conversions=[convert_f_strings_to_strings_format], dry_run=args.dry_run)
        for file in files
    ]

    if any(modified):
        if args.dry_run:
            print(
                "Checked {} files; would have modified {} file{} 😞".format(
                    len(files), sum(modified), "s" if sum(modified) > 1 else ""
                )
            )
        else:
            print(
                "Checked {} files; modified {} file{} 😞".format(
                    len(files), sum(modified), "s" if sum(modified) > 1 else ""
                )
            )
        return 1
    else:
        print("Checked {} files; didn't have to do anything!".format(len(files)))
        return 0


if __name__ == "__main__":
    sys.exit(cli())

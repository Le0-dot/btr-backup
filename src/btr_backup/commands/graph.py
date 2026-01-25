from collections.abc import Generator
from enum import StrEnum
from pathlib import Path
from typing import Any

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


class GraphElement(StrEnum):
    newline = "\n"
    whitespace = " "
    trunk = "┃"
    fork_right = "┣━━"
    trun_down = "━━┓"
    trun_right = "┗━━"


def generate_graph(logical_dirs: dict[str, list[str]]) -> Generator[str, None, None]:
    items = list(logical_dirs.items())

    for logic_dir, subvolumes in items[:-1]:
        yield GraphElement.trunk
        yield GraphElement.newline

        yield GraphElement.fork_right
        yield GraphElement.whitespace
        yield logic_dir
        yield GraphElement.whitespace
        yield GraphElement.trun_down
        yield GraphElement.newline

        padding_len = (
            len(GraphElement.fork_right)
            + len(GraphElement.whitespace)
            + len(logic_dir)
            + len(GraphElement.whitespace)
            + len(GraphElement.trun_down)
            - 1  # trunk
            - 1  # start at the same column
        )
        for subvolume in subvolumes[:-1]:
            yield GraphElement.trunk
            yield GraphElement.whitespace * padding_len
            yield GraphElement.fork_right
            yield GraphElement.whitespace
            yield subvolume
            yield GraphElement.newline

        yield GraphElement.trunk
        yield GraphElement.whitespace * padding_len
        yield GraphElement.trun_right
        yield GraphElement.whitespace
        yield subvolumes[-1]
        yield GraphElement.newline

    logic_dir, subvolumes = items[-1]

    yield GraphElement.trunk
    yield GraphElement.newline

    yield GraphElement.trun_right
    yield GraphElement.whitespace
    yield logic_dir
    yield GraphElement.whitespace
    yield GraphElement.trun_down
    yield GraphElement.newline

    padding_len = (
        len(GraphElement.fork_right)
        + len(GraphElement.whitespace)
        + len(logic_dir)
        + len(GraphElement.whitespace)
        + len(GraphElement.trun_down)
        - 1  # start at the same column
    )
    for subvolume in subvolumes[:-1]:
        yield GraphElement.whitespace * padding_len
        yield GraphElement.fork_right
        yield GraphElement.whitespace
        yield subvolume
        yield GraphElement.newline

    yield GraphElement.whitespace * padding_len
    yield GraphElement.trun_right
    yield GraphElement.whitespace
    yield subvolumes[-1]
    yield GraphElement.newline


def graph_subvolumes(working_dir: Path, **kwargs: Any) -> None:
    logger.debug(f"Listing subvolumes in {working_dir}")

    logical_volumes: dict[str, list[str]] = {}
    for logic_dir in working_dir.iterdir():
        logger.debug(f"Found logical directory: {logic_dir}")

        subvolumes = [subvol.name for subvol in logic_dir.iterdir()]
        logger.debug(f"Found subvolumes: {', '.join(subvolumes)}")

        logical_volumes[logic_dir.name] = sorted(subvolumes, reverse=True)

    print("".join(generate_graph(logical_volumes)))


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "graph",
        help="Graph available subvolumes.",
    )
    parser.set_defaults(func=graph_subvolumes)

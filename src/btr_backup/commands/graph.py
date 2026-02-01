from collections.abc import Iterator
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


class GraphElement(StrEnum):
    newline = "\n"
    whitespace = " "
    trunk = "┃"
    fork_right = "┣━━"
    turn_down = "━━┓"
    turn_right = "┗━━"


def generate_with_last[T, U](
    values: list[T],
    producer: Callable[[T], Iterator[U]],
    last_producer: Callable[[T], Iterator[U]],
) -> Iterator[U]:
    for value in values[:-1]:
        yield from producer(value)
    yield from last_producer(values[-1])


def generate_subvolume_graph(
    subvolumes: list[str],
    padding: int,
    last: bool = False,
) -> Iterator[str]:
    def generator(subvolume: str) -> Iterator[str]:
        yield GraphElement.trunk if not last else GraphElement.whitespace
        yield GraphElement.whitespace * padding
        yield GraphElement.fork_right
        yield GraphElement.whitespace
        yield subvolume
        yield GraphElement.newline

    def last_generator(subvolume: str) -> Iterator[str]:
        yield GraphElement.trunk if not last else GraphElement.whitespace
        yield GraphElement.whitespace * padding
        yield GraphElement.turn_right
        yield GraphElement.whitespace
        yield subvolume
        yield GraphElement.newline

    yield from generate_with_last(subvolumes, generator, last_generator)


def generate_graph(logical_dirs: dict[str, list[str]]) -> Iterator[str]:
    items = list(logical_dirs.items())

    def generator(item: tuple[str, list[str]]) -> Iterator[str]:
        logic_dir, subvolumes = item

        padding = (
            len(GraphElement.fork_right)
            + len(GraphElement.whitespace)
            + len(logic_dir)
            + len(GraphElement.whitespace)
            + len(GraphElement.turn_down)
            - 1  # trunk
            - 1  # start at the same column
        )

        yield GraphElement.trunk
        yield GraphElement.newline

        yield GraphElement.fork_right
        yield GraphElement.whitespace
        yield logic_dir
        yield GraphElement.whitespace
        yield GraphElement.turn_down
        yield GraphElement.newline

        yield from generate_subvolume_graph(subvolumes, padding)

    def last_generator(item: tuple[str, list[str]]) -> Iterator[str]:
        logic_dir, subvolumes = item

        padding = (
            len(GraphElement.fork_right)
            + len(GraphElement.whitespace)
            + len(logic_dir)
            + len(GraphElement.whitespace)
            + len(GraphElement.turn_down)
            - 1  # no trunk
            - 1  # start at the same column
        )

        yield GraphElement.trunk
        yield GraphElement.newline

        yield GraphElement.turn_right
        yield GraphElement.whitespace
        yield logic_dir
        yield GraphElement.whitespace
        yield GraphElement.turn_down
        yield GraphElement.newline

        yield from generate_subvolume_graph(subvolumes, padding, last=True)

    yield from generate_with_last(items, generator, last_generator)


def graph_subvolumes(working_dir: Path, **kwargs: Any) -> None:
    logger.debug(f"Graphing subvolumes in {working_dir}")

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

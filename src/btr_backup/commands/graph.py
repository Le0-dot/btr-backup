from collections.abc import Iterator
from enum import StrEnum
from operator import attrgetter
from pathlib import Path
from typing import Any, Callable

from btr_backup.common import include_exclude
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


def graph_subvolumes(
    workdir: Path,
    *,
    include: list[str],
    exclude: list[str],
    **kwargs: Any,
) -> bool:
    logger.debug(f"Graphing subvolumes in {workdir}")

    directories = include_exclude(
        workdir.iterdir(),
        include,
        exclude,
        attrgetter("name"),
    )
    logger.debug(f"Found subvolume directories: {', '.join(map(str, directories))}")

    structure = {
        subvol_dir.name: sorted(subvol.name for subvol in subvol_dir.iterdir())
        for subvol_dir in directories
    }
    logger.debug(f"Subvolume structure: {structure}")

    print("".join(generate_graph(structure)))

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "graph",
        help="Graph available subvolumes.",
    )

    group = parser.add_mutually_exclusive_group()

    group.add_argument(
        "--include",
        "-i",
        type=str,
        action="append",
        help="Include only specified subvolumes.",
    )
    group.add_argument(
        "--exclude",
        "-e",
        type=str,
        action="append",
        help="Include only subvolumes that were not specified.",
    )

    parser.set_defaults(func=graph_subvolumes)

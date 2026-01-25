from pathlib import Path
from typing import Any

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def make_header(logic_dir: str) -> str:
    return f"┣━━ {logic_dir} ━━┓"


def make_subvolume_line(subvolume: str, left_padding: int) -> str:
    return f"┃{' ' * (left_padding - 2)}┣━━ {subvolume}"


def graph_subvolumes(working_dir: Path, **kwargs: Any) -> None:
    logger.debug(f"Listing subvolumes in {working_dir}")

    logical_volumes: dict[str, list[str]] = {}
    for logic_dir in working_dir.iterdir():
        logger.debug(f"Found logical directory: {logic_dir}")

        subvolumes = [subvol.name for subvol in logic_dir.iterdir()]
        logger.debug(f"Found subvolumes: {', '.join(subvolumes)}")

        logical_volumes[logic_dir.name] = sorted(subvolumes, reverse=True)

    for logic_dir, subvolumes in logical_volumes.items():
        header = make_header(logic_dir)
        print(header)

        for subvolume in subvolumes:
            print(make_subvolume_line(subvolume, len(header)))


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "graph",
        help="Graph available subvolumes.",
    )
    parser.set_defaults(func=graph_subvolumes)

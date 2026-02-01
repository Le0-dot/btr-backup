from argparse import BooleanOptionalAction
from pathlib import Path
from typing import Any

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def list_subvolumes(
    working_dir: Path,
    *,
    logical_dir: str,
    count: bool,
    all: bool,
    **kwargs: Any,
) -> None:
    logger.debug("Listing subvolumes in %s", working_dir)

    logical_volumes: dict[str, list[str]] = {}
    for logic_dir in working_dir.glob(logical_dir):
        logger.debug(f"Found logical directory: {logic_dir}")

        subvolumes = [
            subvol.name for subvol in logic_dir.iterdir() if subvol.name != "active"
        ]
        logger.debug(f"Found subvolumes: {', '.join(subvolumes)}")

        logical_volumes[logic_dir.name] = sorted(subvolumes, reverse=True)

    if not logical_volumes:
        logger.error("No logical directories found.")
        return

    for logic_dir, subvolumes in logical_volumes.items():
        print(f"{logic_dir}", end="\t")

        if count:
            print("total:", len(subvolumes))

        subvolumes_to_show = subvolumes if all else subvolumes[:1]
        for subvol in subvolumes_to_show:
            print(f"\t{subvol}")


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List available subvolumes.",
    )

    parser.add_argument(
        "logical_dir",
        type=str,
        nargs="?",
        default="*",
        help="Logical directory to list subvolumes from.",
    )
    parser.add_argument(
        "--count",
        action=BooleanOptionalAction,
        default=False,
        help="Count snapshots.",
    )
    parser.add_argument(
        "--all",
        action=BooleanOptionalAction,
        default=False,
        help="Show all snapshots.",
    )

    parser.set_defaults(func=list_subvolumes)

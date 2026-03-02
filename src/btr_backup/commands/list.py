from argparse import BooleanOptionalAction
from operator import attrgetter
from pathlib import Path
from typing import Any

from btr_backup.common import include_exclude, snapshots_for
from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def list_subvolumes(
    workdir: Path,
    *,
    include: list[str],
    exclude: list[str],
    count: bool,
    show: bool,
    **kwargs: Any,
) -> bool:
    logger.debug("Listing subvolumes in %s", workdir)

    directories = include_exclude(
        workdir.iterdir(),
        include,
        exclude,
        attrgetter("name"),
    )
    snapshots = {
        subvolume_dir.name: snapshots_for(subvolume_dir)
        for subvolume_dir in directories
    }

    if not snapshots:
        logger.error("No directories found.")
        return False

    for directory, snapshot_list in snapshots.items():
        print(f"{directory}", end="\t")
        print(len(snapshot_list) if count else "")

        for snapshot in snapshot_list if show else []:
            print(f"\t{snapshot}")

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List available subvolumes.",
    )

    parser.add_argument(
        "--count",
        action=BooleanOptionalAction,
        default=True,
        help="Count snapshots.",
    )
    parser.add_argument(
        "--show",
        action=BooleanOptionalAction,
        default=False,
        help="Show snapshots.",
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

    parser.set_defaults(func=list_subvolumes)

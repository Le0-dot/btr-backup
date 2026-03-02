from itertools import chain
from operator import attrgetter
from pathlib import Path
from typing import Any

from btrfsutil import delete_subvolume

from btr_backup.common import include_exclude, snapshots_for
from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def remove_subvolumes(
    workdir: Path,
    *,
    include: list[str],
    exclude: list[str],
    dry_run: bool,
    keep_latest: int,
    **kwargs: Any,
) -> bool:
    logger.debug("Looking up subvolumes in %s", workdir)

    directories = include_exclude(
        workdir.iterdir(),
        include,
        exclude,
        attrgetter("name"),
    )

    if not directories:
        logger.error("No specified directories found.")
        return False

    to_remove = (
        (
            subvolume_dir / snapshot
            for snapshot in snapshots_for(subvolume_dir)[keep_latest:]
        )
        for subvolume_dir in directories
    )

    for snapshot in chain.from_iterable(to_remove):
        logger.debug("%s will be removed", snapshot.relative_to(workdir))

        if not dry_run:
            delete_subvolume(snapshot)

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "remove",
        help="Remove selected subvolumes.",
    )

    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        default=False,
        help="Show what would be removed without actually removing anything.",
    )
    parser.add_argument(
        "--keep-latest",
        type=int,
        default=1,
        help="Number of latest subvolumes to keep.",
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

    parser.set_defaults(func=remove_subvolumes)

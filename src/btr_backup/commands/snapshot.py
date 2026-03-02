from datetime import datetime
from operator import attrgetter
from pathlib import Path
from typing import Any

from btrfsutil import create_snapshot, is_subvolume

from btr_backup.common import include_exclude
from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def snapshot_subvolumes(
    workdir: Path,
    *,
    include: list[str],
    exclude: list[str],
    **kwargs: Any,
) -> bool:
    logger.debug("Listing subvolumes in %s", workdir)

    direcotries = include_exclude(
        workdir.iterdir(),
        include,
        exclude,
        attrgetter("name"),
    )

    if not direcotries:
        logger.error("No specified directories found.")
        return False

    active = [directory / "active" for directory in direcotries]

    if not all(is_subvolume(path) for path in active):
        logger.error("Some active subvolumes are missing.")
        return False

    snapshot_name = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%:z")

    snapshots = [directory / snapshot_name for directory in direcotries]

    if not all(not path.exists() for path in snapshots):
        logger.error("Some snapshots already exist.")
        return False

    for source, destination in zip(active, snapshots):
        logger.debug("Creating snapshot %s from %s", destination, source)
        create_snapshot(source, destination, read_only=True)

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "snapshot",
        help="Snapshot selected subvolumes.",
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

    parser.set_defaults(func=snapshot_subvolumes)

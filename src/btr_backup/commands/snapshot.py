from datetime import datetime
from pathlib import Path
from typing import Any

from btrfsutil import create_snapshot

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def snapshot_subvolumes(working_dir: Path, logical_dir: str, **kwargs: Any) -> None:
    logger.debug("Listing subvolumes in %s", working_dir)

    direcotries = list(working_dir.glob(logical_dir))

    if not direcotries:
        logger.error("No active subvolumes found.")
        return

    active = [directory / "active" for directory in direcotries]

    if not all(path.is_dir() for path in active):
        logger.error("Some active subvolumes are missing.")
        return

    snapshot_name = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%:z")

    snapshots = [directory / snapshot_name for directory in direcotries]

    if not all(not path.exists() for path in snapshots):
        logger.error("Some snapshots already exist.")
        return

    for src, dst in zip(active, snapshots):
        logger.debug("Creating snapshot from %s to %s", src, dst)
        create_snapshot(src, dst, read_only=True)


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "snapshot",
        help="Snapshot selected subvolumes.",
    )

    parser.add_argument(
        "logical_dir",
        type=str,
        nargs="?",
        default="*",
        help="Logical directory to snapshot subvolumes from.",
    )

    parser.set_defaults(func=snapshot_subvolumes)

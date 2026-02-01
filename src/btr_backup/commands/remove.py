from pathlib import Path
from typing import Any

from btrfsutil import delete_subvolume

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def remove_subvolumes(
    working_dir: Path,
    *,
    logical_dir: str,
    dry_run: bool,
    keep_latest: int,
    **kwargs: Any,
) -> None:
    logger.debug("Looking up subvolumes in %s", working_dir)

    directories = list(working_dir.glob(logical_dir))

    if not directories:
        logger.error("No specified directories found.")
        return

    for directory in directories:
        subvolumes = sorted(
            [subvol for subvol in directory.iterdir() if subvol.name != "active"],
            reverse=True,
        )
        to_remove = subvolumes[keep_latest:]

        for subvol in to_remove:
            logger.warning("%s will be removed", Path(subvol.parent.name) / subvol.name)

            if not dry_run:
                delete_subvolume(subvol)


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "remove",
        help="Remove selected subvolumes.",
    )

    parser.add_argument(
        "logical_dir",
        type=str,
        nargs="?",
        default="*",
        help="Logical directory to remove subvolumes from.",
    )
    parser.add_argument(
        "--dry-run",
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

    parser.set_defaults(func=remove_subvolumes)

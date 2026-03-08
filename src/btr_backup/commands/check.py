from datetime import datetime
from itertools import filterfalse
from operator import attrgetter
from pathlib import Path
from typing import Any

from btrfsutil import is_subvolume

from btr_backup.common import include_exclude
from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def datetime_like(date: str, fmt: str) -> bool:
    try:
        datetime.strptime(date, fmt)
    except ValueError:
        return False
    return True


def check_subvolume_name(subvolume: Path) -> bool:
    return subvolume.name == "active" or datetime_like(
        subvolume.name, "%Y-%m-%dT%H:%M:%S%z"
    )


def check_structure(
    workdir: Path,
    *,
    include: list[str],
    exclude: list[str],
    **kwargs: Any,
) -> bool:
    logger.info(f"Verifying {workdir.name} existence")
    if not workdir.exists():
        logger.error(f"Path {workdir} does not exist.")
        return False

    logger.info(f"Verifying {workdir.name} is a directory")
    if not workdir.is_dir():
        logger.error(f"Path {workdir} is not a directory.")
        return False

    directories = include_exclude(
        workdir.iterdir(),
        include,
        exclude,
        attrgetter("name"),
    )
    for directory in directories:
        logger.info(f"Verifying {directory} is a directory")
        if not directory.is_dir():
            logger.error(f"Path {directory} is not a directory.")
            return False

        logger.info(f"Verifying contents of {directory} are subvolumes")
        if extra := list(filterfalse(is_subvolume, directory.iterdir())):
            extra_str = ", ".join(str(p) for p in extra)
            logger.error(f"Only subvolumes allowed in {directory}: {extra_str}")
            return False

        logger.info(f"Verifying contents of {directory} are named correctly")
        if invalid := list(filterfalse(check_subvolume_name, directory.iterdir())):
            invalid_str = ", ".join(str(p) for p in invalid)
            logger.error(f"Invalid subvolume names in {directory}: {invalid_str}")
            return False

    logger.info("Structure is valid.")

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "check",
        help="Check subvolumes structure.",
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

    parser.set_defaults(func=check_structure)

from datetime import datetime
from itertools import filterfalse
from pathlib import Path
from typing import Any

from btrfsutil import is_subvolume

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


def check_structure(working_dir: Path, **kwargs: Any) -> bool:
    if not working_dir.exists():
        logger.error(f"Path {working_dir} does not exist.")
        return False

    if not working_dir.is_dir():
        logger.error(f"Path {working_dir} is not a directory.")
        return False

    for logic_dir in working_dir.iterdir():
        if not logic_dir.is_dir():
            logger.error(f"Path {logic_dir} is not a directory.")
            return False

        if extra := list(filterfalse(is_subvolume, logic_dir.iterdir())):
            extra_str = ", ".join(str(p) for p in extra)
            logger.error(f"Only subvolumes allowed in {logic_dir}: {extra_str}")
            return False

        if invalid := list(filterfalse(check_subvolume_name, logic_dir.iterdir())):
            invalid_str = ", ".join(str(p) for p in invalid)
            logger.error(f"Invalid subvolume names in {logic_dir}: {invalid_str}")
            return False

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "check",
        help="Check subvolumes structure.",
    )
    parser.set_defaults(func=check_structure)

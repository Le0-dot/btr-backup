from pathlib import Path
from typing import Any

from btr_backup.protocols import Subparsers


def check_structure(working_dir: Path, **kwargs: Any) -> None:
    pass


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "check",
        help="Check subvolumes structure.",
    )
    parser.set_defaults(func=check_structure)

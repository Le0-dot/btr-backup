from pathlib import Path
from typing import Any

from btr_backup.protocols import Subparsers


def list_subvolumes(working_dir: Path, **kwargs: Any) -> None:
    pass


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List available subvolumes.",
    )
    parser.set_defaults(func=list_subvolumes)

from pathlib import Path
from typing import Any

from btr_backup.protocols import Subparsers


def snapshot_subvolumes(working_dir: Path, **kwargs: Any) -> None:
    pass


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "snapshot",
        help="Snapshot selected subvolumes.",
    )
    parser.set_defaults(func=snapshot_subvolumes)

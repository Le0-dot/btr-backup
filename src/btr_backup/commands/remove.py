from argparse import Namespace
from pathlib import Path

from btr_backup.protocols import Subparsers


def remove_subvolumes(working_dir: Path, args: Namespace) -> None:
    pass


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "remove",
        help="Remove selected subvolumes.",
    )
    parser.set_defaults(func=remove_subvolumes)

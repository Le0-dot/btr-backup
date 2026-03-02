from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from contextlib import ExitStack
from pathlib import Path
from sys import exit
from tempfile import TemporaryDirectory

from btr_backup.commands import add_commands
from btr_backup.common import block_device, mount_context
from btr_backup.log import logger, setup_logger


def parse_args(args: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser(description="Utility for backing up btrfs subvolumes.")

    parser.add_argument(
        "--dev",
        type=block_device,
        required=True,
        help="Path to the btrfs disk/partition.",
    )
    parser.add_argument(
        "--chdir",
        type=Path,
        default=Path(),
        help="Directory on the btrfs disk/partition with subvolume structure.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Enable verbose logging.",
    )

    subparsers = parser.add_subparsers(required=True)
    add_commands(subparsers)

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()

    setup_logger(logger, verbosity=args.verbose)

    logger.debug("Parsed arguments: %s", args)

    with ExitStack() as stack:
        temp_dir = stack.enter_context(TemporaryDirectory(prefix="btr-backup-"))

        try:
            mount_point = stack.enter_context(
                mount_context(args.dev, temp_dir, "btrfs")
            )
        except OSError as e:
            logger.error(
                "Failed to mount %s device to %s: %s", args.dev, temp_dir, e.strerror
            )
            return

        workdir = mount_point / args.chdir
        if not workdir.exists():
            logger.error(
                "The specified working directory %s does not exist on the mounted device.",
                args.chdir,
            )
            return

        if not args.func(workdir, **vars(args)):
            exit(1)

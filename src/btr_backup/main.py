from argparse import ArgumentParser, ArgumentTypeError, Namespace
from collections.abc import Iterator, Sequence
from contextlib import ExitStack, contextmanager
from os import PathLike, fspath
from pathlib import Path
from sys import exit
from tempfile import TemporaryDirectory

from mount import mount, umount

from btr_backup.commands import (
    add_check_command,
    add_list_command,
    add_remove_command,
    add_snapshot_command,
)
from btr_backup.log import logger, setup_logger


def block_device(arg: str) -> Path:
    path = Path(arg)

    if not path.exists():
        raise ArgumentTypeError(f"{path} does not exist.")

    # if not path.is_block_device():
    #     raise ArgumentTypeError(f"{path} is not a block device.")

    return path


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

    add_check_command(subparsers)
    add_list_command(subparsers)
    add_remove_command(subparsers)
    add_snapshot_command(subparsers)

    return parser.parse_args(args)


@contextmanager
def mount_context(device: PathLike, destination: PathLike, fs: str) -> Iterator[Path]:
    mount(fspath(device), fspath(destination), fs)
    try:
        yield Path(destination)
    finally:
        umount(fspath(destination))


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

        if not args.func(mount_point / args.chdir, **vars(args)):
            exit(1)

import logging
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from collections.abc import Iterator, Sequence
from contextlib import ExitStack, contextmanager
from os import PathLike, fspath
from pathlib import Path
from tempfile import TemporaryDirectory

from mount import mount, umount

logging.basicConfig(format="[%(levelname)s] %(message)s")


def block_device(arg: str) -> Path:
    path = Path(arg)

    if not path.exists():
        raise ArgumentTypeError(f"{path} does not exist.")

    if not path.is_block_device():
        raise ArgumentTypeError(f"{path} is not a block device.")

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

    check_parser = subparsers.add_parser(
        "check",
        help="Check subvolumes structure.",
    )
    check_parser.set_defaults(func=check_structure)

    list_parser = subparsers.add_parser(
        "list",
        help="List available subvolumes.",
    )
    list_parser.set_defaults(func=list_subvolumes)

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Snapshot subvolumes.",
    )
    snapshot_parser.set_defaults(func=snapshot_subvolumes)

    remove_parser = subparsers.add_parser(
        "remove",
        help="Remove selected subvolumes.",
    )
    remove_parser.set_defaults(func=remove_subvolumes)

    move_parser = subparsers.add_parser(
        "move",
        help="Move subvolumes to another filesystem.",
    )
    move_parser.set_defaults(func=move_subvolumes)

    return parser.parse_args(args)


def check_structure(working_dir: Path, args: Namespace) -> None:
    pass


def list_subvolumes(working_dir: Path, args: Namespace) -> None:
    pass


def snapshot_subvolumes(working_dir: Path, args: Namespace) -> None:
    pass


def remove_subvolumes(working_dir: Path, args: Namespace) -> None:
    pass


def move_subvolumes(working_dir: Path, args: Namespace) -> None:
    pass


@contextmanager
def mount_context(device: PathLike, destination: PathLike, fs: str) -> Iterator[Path]:
    mount(fspath(device), fspath(destination), fs)
    try:
        yield Path(destination)
    finally:
        umount(fspath(destination))


def main() -> None:
    args = parse_args()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING - (10 * min(args.verbose, 2)))

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

        args.func(mount_point / args.chdir, args)

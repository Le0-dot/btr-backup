from contextlib import ExitStack
from operator import attrgetter
from pathlib import Path
from subprocess import DEVNULL, run
from tempfile import TemporaryDirectory, TemporaryFile
from typing import IO, Any

from btr_backup.common import (
    block_device,
    include_exclude,
    mount_context,
    snapshots_for,
)
from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def btrfs_progs_available() -> bool:
    command = ["btrfs", "--help"]
    return run(command, stdout=DEVNULL, stderr=DEVNULL).returncode == 0


def btrfs_send(subvol: Path, parent: Path | None, stdout: IO[bytes]) -> bool:
    command = ["btrfs", "send", str(subvol)]
    if parent:
        command.extend(["-p", str(parent)])

    return run(command, stdout=stdout, stderr=DEVNULL).returncode == 0


def btrfs_receive(path: Path, stdin: IO[bytes]) -> bool:
    command = ["btrfs", "receive", str(path)]
    return run(command, stdin=stdin, stdout=DEVNULL, stderr=DEVNULL).returncode == 0


def last_snapshot(dir: Path) -> Path | None:
    subvols = snapshots_for(dir)
    return dir / subvols[0] if subvols else None


def upload_snapshot(source: Path, destination: Path) -> bool:
    logger.debug("Processing logical directory: %s", source)

    snapshot = last_snapshot(source)
    if not snapshot:
        logger.warning("No snapshots found in %s, skipping.", source)
        return True

    destination.mkdir(exist_ok=True)

    destination_snapshot = last_snapshot(destination)
    if destination_snapshot and destination_snapshot.name == snapshot.name:
        logger.warning(
            "Snapshot %s already exists in destination, skipping.",
            snapshot.name,
        )
        return True

    parent = None
    if destination_snapshot:
        parent = snapshot.with_name(destination_snapshot.name)

    with TemporaryFile(prefix="btr-backup-") as buffer:
        logger.debug("Uploading snapshot %s, parent snapshot %s", snapshot, parent)
        if not btrfs_send(snapshot, parent, buffer):
            logger.error(
                "Failed to send snapshot %s to temporary file.",
                snapshot.stem,
            )
            return False

        buffer.seek(0)

        if not btrfs_receive(destination, buffer):
            logger.error(
                "Failed to receive snapshot from temporary file to %s.",
                destination,
            )
            return False

    return True


def upload_snapshots(
    workdir: Path,
    *,
    include: list[str],
    exclude: list[str],
    dest_dev: Path,
    dest_chdir: Path,
    **kwargs: Any,
) -> bool:
    if not btrfs_progs_available():
        logger.error("btrfs-progs not available.")
        return False

    with ExitStack() as stack:
        temp_dir = stack.enter_context(TemporaryDirectory(prefix="btr-backup-"))

        try:
            mount_point = stack.enter_context(
                mount_context(dest_dev, temp_dir, "btrfs")
            )
        except OSError as e:
            logger.error(
                "Failed to mount %s device to %s: %s", dest_dev, temp_dir, e.strerror
            )
            return False

        dest_workdir = mount_point / dest_chdir
        if not dest_workdir.exists():
            logger.error(
                "Destination working directory %s does not exist.",
                dest_workdir,
            )
            return False

        directories = include_exclude(
            workdir.iterdir(),
            include,
            exclude,
            attrgetter("name"),
        )

        return all(
            upload_snapshot(directory, dest_workdir / directory.name)
            for directory in directories
        )


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "upload",
        help="Copy snapshots from one btrfs filesystem to another.",
    )

    parser.add_argument(
        "--dest-dev",
        type=block_device,
        required=True,
        help="Destination block device to copy snapshots to.",
    )
    parser.add_argument(
        "--dest-chdir",
        type=Path,
        default=Path(),
        help="Directory on destination block device with directory structure.",
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

    parser.set_defaults(func=upload_snapshots)

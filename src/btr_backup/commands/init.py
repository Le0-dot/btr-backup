from os import fspath
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

from btrfsutil import create_subvolume, subvolume_id
from mount import mount

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def init(
    workdir: Path,
    *,
    dev: Path,
    dir: str,
    mount_dir: Path | str | None,
    **kwargs: Any,
) -> bool:
    logger.debug("Initializing subvolume directory %s in %s", dir, workdir)

    directory_path = workdir / dir

    if directory_path.exists():
        logger.error("Logical directory already exists.")
        return False

    directory_path.mkdir()

    active_subvolume_path = directory_path / "active"
    create_subvolume(active_subvolume_path)

    logger.info("Logical directory %s initialized successfully.", directory_path)

    if not mount_dir:
        return True

    logger.debug("Mounting logical directory %s", directory_path)

    if isinstance(mount_dir, str):
        mount_dir = Path(mkdtemp(prefix="btr-backup-"))

    mount_dir.mkdir(exist_ok=True, parents=True)

    subvolid = subvolume_id(active_subvolume_path)
    logger.debug("Subvolume ID for %s is %d", directory_path, subvolid)

    try:
        mount(fspath(dev), fspath(mount_dir), "btrfs", data=f"subvolid={subvolid}")
    except OSError as e:
        logger.error("Failed to mount logical directory: %s", e)
        return False

    logger.info("Logical directory %s mounted successfully at %s.", dir, mount_dir)

    print(mount_dir)

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "init",
        help="Initialize a logical directory for subvolumes.",
    )

    parser.add_argument(
        "dir",
        type=str,
        help="Directory for subvolume and snapshots to create.",
    )
    parser.add_argument(
        "--mount-dir",
        "-m",
        type=Path,
        nargs="?",
        const="auto",
        help="Mount the logical directory after initialization.",
    )

    parser.set_defaults(func=init)

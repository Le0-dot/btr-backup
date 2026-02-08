from os import fspath
from pathlib import Path
from typing import Any

from btrfsutil import create_subvolume, subvolume_id
from mount import mount

from btr_backup.log import logger
from btr_backup.protocols import Subparsers


def init(
    working_dir: Path,
    *,
    dev: Path,
    logical_dir: str,
    mount_path: Path | None,
    **kwargs: Any,
) -> bool:
    logger.debug("Initializing logical directory %s in %s", logical_dir, working_dir)

    logical_dir_path = working_dir / logical_dir

    if logical_dir_path.exists():
        logger.error("Logical directory already exists.")
        return False

    logical_dir_path.mkdir()

    active_subvolume_path = logical_dir_path / "active"
    create_subvolume(active_subvolume_path)

    logger.info("Logical directory %s initialized successfully.", logical_dir_path)

    if not mount_path:
        return True

    logger.debug("Mounting logical directory %s", logical_dir_path)

    if not mount_path.exists():
        logger.debug("Mount path %s does not exist, creating it.", mount_path)
        mount_path.mkdir()

    subvolid = subvolume_id(active_subvolume_path)
    logger.debug("Subvolume ID for %s is %d", logical_dir_path, subvolid)

    try:
        mount(fspath(dev), fspath(mount_path), "btrfs", data=f"subvolid={subvolid}")
    except OSError as e:
        logger.error("Failed to mount logical directory: %s", e)
        return False

    logger.info(
        "Logical directory %s mounted successfully at %s.", logical_dir_path, mount_path
    )

    return True


def add_command(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "init",
        help="Initialize a logical directory for subvolumes.",
    )

    parser.add_argument(
        "logical_dir",
        type=str,
        help="Logical directory to create.",
    )
    parser.add_argument(
        "--mount-path",
        type=Path,
        help="Mount the logical directory after initialization.",
    )

    parser.set_defaults(func=init)

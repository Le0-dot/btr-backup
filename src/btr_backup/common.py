from argparse import ArgumentTypeError
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from os import PathLike, fspath
from pathlib import Path

from mount import mount, umount


def block_device(arg: str) -> Path:
    path = Path(arg)

    if not path.exists():
        raise ArgumentTypeError(f"{path} does not exist.")

    if not path.is_block_device():
        raise ArgumentTypeError(f"{path} is not a block device.")

    return path


@contextmanager
def mount_context(device: PathLike, destination: PathLike, fs: str) -> Iterator[Path]:
    mount(fspath(device), fspath(destination), fs)
    try:
        yield Path(destination)
    finally:
        with suppress(OSError):
            umount(fspath(destination))


def snapshots(dir: Path) -> list[str]:
    return sorted(
        [snapshot.name for snapshot in dir.iterdir() if snapshot.name != "active"],
        reverse=True,
    )

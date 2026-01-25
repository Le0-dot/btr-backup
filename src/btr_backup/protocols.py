from argparse import ArgumentParser
from typing import Any, Protocol


class Subparsers(Protocol):
    def add_parser(self, name: str, *, help: str, **kwargs: Any) -> ArgumentParser: ...

from btr_backup.commands.check import add_command as add_check_command
from btr_backup.commands.graph import add_command as add_graph_command
from btr_backup.commands.init import add_command as add_init_command
from btr_backup.commands.list import add_command as add_list_command
from btr_backup.commands.remove import add_command as add_remove_command
from btr_backup.commands.snapshot import add_command as add_snapshot_command
from btr_backup.protocols import Subparsers


def add_commands(subparsers: Subparsers) -> None:
    add_command_list = [
        add_check_command,
        add_graph_command,
        add_init_command,
        add_list_command,
        add_remove_command,
        add_snapshot_command,
    ]
    for add_command in add_command_list:
        add_command(subparsers)

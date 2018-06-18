import click
import inspect

from ecstools.lib.cli import MyCLI, current_dir


wk_file = inspect.getfile(inspect.currentframe())


class SubCommand(MyCLI):
    plugin_folder = current_dir(wk_file)


@click.group(cls=SubCommand)
@click.pass_context
def cli(ctx):
    """Manage task definitions"""
    pass

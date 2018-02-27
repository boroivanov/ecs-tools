import os
import sys
import click
import string
import inspect

wk_file = inspect.getfile(inspect.currentframe())
wk_dir = os.path.dirname(os.path.abspath(wk_file))
sub_dir = wk_file[:-3]
plugin_folder = os.path.join(wk_dir, sub_dir)


class MyServiceCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        alpha = string.ascii_letters
        for filename in os.listdir(plugin_folder):
            if filename.startswith(tuple(alpha)) and filename.endswith('.py'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        if not os.path.isfile(fn):
            click.echo('Command not found')
            sys.exit(0)
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']


@click.group(cls=MyServiceCLI)
@click.pass_context
def cli(ctx):
    """Manage and deploy services"""
    pass

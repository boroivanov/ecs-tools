import os
import click

wk_dir = os.path.dirname(os.path.realpath('__file__'))
plugin_folder = os.path.join(wk_dir, 'cli/commands/task-definition')


class MyTaskDefinitionCLI(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']


@click.group(cls=MyTaskDefinitionCLI)
@click.pass_context
def cli(ctx):
    """Manage task definitions"""
    pass

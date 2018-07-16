import os
import sys
import click
import string


class AliasedGroup(click.Group):

    def get_command(self, ctx, cmd_name):
        """
        Check if alias is defined in the config.
        Otherwise, check if any of the subcommands start with the passed
        command.
        """
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Too many matches: %s' % ', '.join(sorted(matches)))


class Subcommand(click.MultiCommand):
    plugin_folder = os.path.dirname(os.path.realpath(__file__))

    def list_commands(self, ctx):
        rv = []
        alpha = string.ascii_letters
        for filename in os.listdir(self.plugin_folder):
            if filename.startswith(tuple(alpha)) and filename.endswith('.py'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(self.plugin_folder, name + '.py')
        if not os.path.isfile(fn):
            click.echo('Command not found: %s' % name)
            sys.exit(0)
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns[name]

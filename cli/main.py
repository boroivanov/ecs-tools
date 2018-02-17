import os
import boto3
import click

version = '0.0.1'

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')


class MyCLI(click.MultiCommand):

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


@click.group(cls=MyCLI)
@click.pass_context
@click.version_option(version=version, message=version)
@click.option('-p', '--profile', help='AWS profile')
@click.option('-r', '--region', help='AWS region')
def cli(ctx, region, profile):
    """AWS ECS deploy tools"""
    session = boto3.session.Session(profile_name=profile, region_name=region)
    ecs = session.client('ecs')
    ctx.obj = {
        'region': region,
        'profile': profile,
        'ecs': ecs
    }
    pass


if __name__ == '__main__':
    cli()

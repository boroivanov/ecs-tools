import os
import sys
import boto3
import click

from botocore.exceptions import ProfileNotFound, NoRegionError
from ecstools.lib.cli import MyCLI

version = '0.1.3'

commands_dir = os.path.join(os.path.dirname(__file__), 'commands')


class Commands(MyCLI):
    plugin_folder = commands_dir


@click.group(cls=Commands)
@click.pass_context
@click.version_option(version=version, message=version)
@click.option('-p', '--profile', help='AWS profile')
@click.option('-r', '--region', help='AWS region')
def cli(ctx, region, profile):
    """AWS ECS deploy tools"""
    try:
        sess = boto3.session.Session(profile_name=profile, region_name=region)
    except ProfileNotFound as e:
        click.echo(e, err=True)
        sys.exit(1)

    try:
        ecs = sess.client('ecs')
        ecr = sess.client('ecr')
        elbv2 = sess.client('elbv2')
    except NoRegionError as e:
        click.echo(e, err=True)
        sys.exit(1)

    ctx.obj = {
        'region': region,
        'profile': profile,
        'ecs': ecs,
        'ecr': ecr,
        'elbv2': elbv2
    }
    pass


if __name__ == '__main__':
    cli()

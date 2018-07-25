import click

import ecstools.lib.utils as utils
from ecstools.lib.config import config


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.option('-g', '--group', is_flag=True, help='Monitor group')
@click.pass_context
def top(ctx, cluster, service, group):
    """Monitor service"""
    ecs = ctx.obj['ecs']
    elbv2 = ctx.obj['elbv2']

    if group:
        if service in config['service-group']:
            service = config['service-group'][service].split(' ')

    utils.monitor_deployment(ecs, elbv2, cluster, service)

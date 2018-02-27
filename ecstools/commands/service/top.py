import click

import ecstools.lib.utils as utils


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.pass_context
def cli(ctx, cluster, service):
    """Monitor service"""
    ecs = ctx.obj['ecs']
    elbv2 = ctx.obj['elbv2']
    utils.monitor_deployment(ecs, elbv2, cluster, service)

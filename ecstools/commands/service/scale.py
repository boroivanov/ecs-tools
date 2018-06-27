import click

import ecstools.lib.utils as utils


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.argument('count', type=int)
@click.pass_context
def cli(ctx, cluster, service, count):
    """Scale service"""
    ecs = ctx.obj['ecs']
    elbv2 = ctx.obj['elbv2']

    params = {
        'cluster': cluster,
        'service': service,
        'desiredCount': count

    }
    utils.update_service(ecs, **params)
    utils.monitor_deployment(ecs, elbv2, cluster, service)

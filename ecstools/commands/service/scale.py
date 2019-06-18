import click

from ecstools.resources.service import Service
import ecstools.lib.utils as utils


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.argument('count', type=int)
@click.pass_context
def scale(ctx, cluster, service, count):
    """Scale service"""
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']
    elbv2 = ctx.obj['elbv2']

    srv = Service(ecs, ecr, cluster, service)

    params = {
        'cluster': cluster,
        'service': service,
        'desiredCount': count

    }
    srv.update_service(**params)
    utils.monitor_deployment(ecs, elbv2, cluster, service,
                             exit_on_complete=True)

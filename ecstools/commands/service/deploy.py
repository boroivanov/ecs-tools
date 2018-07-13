import click

from ecstools.resources.service import Service
import ecstools.lib.utils as utils


@click.command(short_help='Deploy service')
@click.argument('cluster')
@click.argument('service')
@click.argument('tags', nargs=-1)
@click.option('-c', '--count', type=int, default=None,
              help='Update the current number of tasks')
@click.pass_context
def deploy(ctx, cluster, service, tags, count):
    """Deploy a task definition to a service

    |\b
    The deployment respects the current number of tasks in the service.
    Use '-c' to scale in or out during deploy.
    """
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']
    elbv2 = ctx.obj['elbv2']

    srv = Service(ecs, ecr, cluster, service)
    srv.deploy_tags(tags, count)

    click.echo()
    utils.monitor_deployment(ecs, elbv2, cluster, service)

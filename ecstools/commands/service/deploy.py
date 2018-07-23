import click

from ecstools.resources.service import Service
import ecstools.lib.utils as utils
from ecstools.lib.config import config


@click.command(short_help='Deploy service')
@click.argument('cluster')
@click.argument('service')
@click.argument('tags', nargs=-1)
@click.option('-g', '--group', is_flag=True, help='Run group deployment')
@click.option('-c', '--count', type=int, default=None,
              help='Update the current number of tasks')
@click.pass_context
def deploy(ctx, cluster, service, tags, group, count):
    """Deploy a task definition to a service

    |\b
    The deployment respects the current number of tasks in the service.
    Use '-c' to scale in or out during deploy.
    """
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']
    elbv2 = ctx.obj['elbv2']

    if group:
        run_group_deployment(ecs, ecr, elbv2, cluster, service, tags, count)
    else:
        run_service_deployment(ecs, ecr, elbv2, cluster, service, tags, count)


def deploy_service(ecs, ecr, cluster, service, tags, count):
    srv = Service(ecs, ecr, cluster, service)
    srv.deploy_tags(tags, count)


def run_service_deployment(ecs, ecr, elbv2, cluster, service, tags, count):
    deploy_service(ecs, ecr, cluster, service, tags, count)

    click.echo()
    utils.monitor_deployment(ecs, elbv2, cluster, service)


def run_group_deployment(ecs, ecr, elbv2, cluster, service, tags, count):
    if service in config['service-group']:
        services = config['service-group'][service].split(' ')

        for srv in services:
            pass
            # deploy_service(ecs, ecr, cluster, service, tags, count)
        utils.monitor_group_deployment(ecs, elbv2, cluster, services)
    else:
        click.echo('Deployment group not found in config.')

import sys
import click

from ecstools.resources.service import Service
import ecstools.lib.utils as utils


@click.command(short_help='Deploy service')
@click.argument('cluster')
@click.argument('service')
@click.argument('tags', nargs=-1)
@click.option('-g', '--group', is_flag=True, help='Run group deployment')
@click.option('-c', '--count', type=int, default=None,
              help='Update the current number of tasks')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode')
@click.pass_context
def deploy(ctx, cluster, service, tags, group, count, verbose):
    """Deploy a task definition to a service

    |\b
    The deployment respects the current number of tasks in the service.
    Use '-c' to scale in or out during deploy.
    """
    if len(tags) == 0:
        click.echo('Error: Specify one or more tags to be deployed.', err=True)
        sys.exit(1)

    if group:
        services = utils.get_group_services(service)
        service = run_group_deployment(ctx, cluster, services, tags,
                                       count, verbose)
    else:
        deploy_service(ctx, cluster, service, tags, count, verbose)

    utils.monitor_deployment(ctx.obj['ecs'], ctx.obj['elbv2'],
                             cluster, service, exit_on_complete=True)


def deploy_service(ctx, cluster, service, tags, count, verbose):
    srv = Service(ctx.obj['ecs'], ctx.obj['ecr'], cluster, service)
    srv.deploy_tags(tags, count, verbose)


def run_group_deployment(ctx, cluster, services, tags, count, verbose):
    for srv in services:
        deploy_service(ctx, cluster, srv, tags, count, verbose)
    return services

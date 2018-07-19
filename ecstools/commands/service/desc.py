import click

from ecstools.resources.service import Service
import ecstools.lib.utils as utils


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.pass_context
def desc(ctx, cluster, service):
    """Describe service"""
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']
    elbv2 = ctx.obj['elbv2']

    srv = Service(ecs, ecr, cluster, service)

    print_service_general_info(srv)
    print_service_container_info(srv)
    print_service_load_balancer_info(srv, elbv2)
    print_service_network_info(srv)


def print_service_general_info(srv):
    general_info = (
        srv.cluster(),
        srv.name(),
        srv.task_definition().revision(),
        srv.service()['launchType']
    )
    counts = (
        srv.service()['desiredCount'],
        srv.service()['runningCount'],
        srv.service()['pendingCount']
    )
    click.secho('%s %s %s %s' % (general_info), fg='blue')
    click.secho(('Desired: %s Running: %s Pending: %s' %
                 (counts)), fg='white')


def print_service_container_info(srv):
    for c in srv.task_definition().containers():
        img = srv.task_definition().image(c)
        click.echo('Container:        %s @ ' % c['name'], nl=False)
        click.echo('%s:%s' % (img['image'], img['tag']))


def print_service_load_balancer_info(srv, elbv2):
    for lb in srv.service()['loadBalancers']:
        if 'targetGroupArn' in lb:
            tg_info = utils.describe_target_group_info(elbv2, lb)
            click.echo(
                'Target Group:     ' +
                '{group} {container} {port} {states}'.format(**tg_info))


def print_service_network_info(srv):
    nc = srv.service()['networkConfiguration']['awsvpcConfiguration']
    created_at = srv.service()['createdAt'].replace(microsecond=0)
    click.echo('Subnets:          %s' % ' '.join(nc['subnets']))
    click.echo('Security Groups:  %s' % ' '.join(nc['securityGroups']))
    click.echo('Public IP:        %s' % nc['assignPublicIp'])
    click.echo('Created:          %s' % created_at)

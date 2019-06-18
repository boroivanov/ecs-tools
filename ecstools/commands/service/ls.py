import click
import sys

from botocore.exceptions import ClientError

from ecstools.resources.service import Service


@click.command()
@click.argument('cluster')
@click.option('-a', '--all-stats', is_flag=True, help='Show more info')
@click.option('-A', '--arn', is_flag=True, help='Show ARN')
@click.pass_context
def ls(ctx, cluster, all_stats, arn):
    """List services"""
    ecs = ctx.obj['ecs']
    ecr = ctx.obj['ecr']

    services = list_services(ecs, cluster)

    if not arn:
        services = sorted(map(lambda x: x.split('/')[-1], services))

    for srv in services:
        if all_stats and not arn:
            service = Service(ecs, ecr, cluster, srv)
            print_service_info(service)
        else:
            click.echo(srv)


def list_services(ecs, cluster):
    try:
        response = ecs.list_services(cluster=cluster, maxResults=100)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ClusterNotFoundException':
            click.echo('Cluster not found.', err=True)
        else:
            click.echo(e, err=True)
        sys.exit(1)

    services = response['serviceArns']
    while True:
        if 'nextToken' not in response:
            break
        response = ecs.list_services(
            cluster=cluster,
            maxResults=100,
            nextToken=response['nextToken']
        )
        services += response['serviceArns']

    return services


def print_service_info(srv):
    images = srv.task_definition().images()
    click.echo('{srv_name:32} {task_def:48} {running:3}/{desired:<3} '.format(
        srv_name=srv.name(),
        task_def=srv.task_definition().revision(),
        running=srv.service()['runningCount'],
        desired=srv.service()['desiredCount'],
    ), nl=False
    )
    click.echo('{cpu} {memory} {images}'.format(
        cpu=srv.task_definition().cpu(),
        memory=srv.task_definition().memory(),
        images=' '.join('{}:{}'.format(i['image'], i['tag']) for i in images)
    )
    )

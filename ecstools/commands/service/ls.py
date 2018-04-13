import click
import sys

from botocore.exceptions import ClientError


@click.command()
@click.argument('cluster')
@click.option('-a', '--all-stats', is_flag=True, help='Show more info')
@click.option('-A', '--arn', is_flag=True, help='Show ARN')
@click.pass_context
def cli(ctx, cluster, all_stats, arn):
    """List services"""
    ecs = ctx.obj['ecs']
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

    if not arn:
        services = sorted(map(lambda x: x.split('/')[-1], services))

    for srv in services:
        if all_stats:
            s = describe_service(ecs, cluster, srv)
            td = get_task_definition(ecs, s['taskDefinition'])
            containers = td['containerDefinitions']

            click.echo('{srv_name:32} {task_def:48} {running:3}/{desired:<3} {cpu} {memory} {image}'.format(
                srv_name=s['serviceName'],
                task_def=s['taskDefinition'].split('/')[-1],
                running=s['runningCount'],
                desired=s['desiredCount'],
                cpu=td['cpu'],
                memory=td['memory'],
                image=' '.join('{}'.format(
                    c['image'].split('/')[1]) for c in containers)
            )
            )
        else:
            click.echo(srv)


def describe_service(ecs, cluster, service):
    try:
        response = ecs.describe_services(
            cluster=cluster,
            services=[service]
        )
        service = response['services'][0]
    except ClientError as e:
        if e.response['Error']['Code'] == 'ClusterNotFoundException':
            click.echo('Cluster not found.', err=True)
        else:
            click.echo(e, err=True)
        sys.exit(1)
    except:
        click.echo('Service not found.', err=True)
        sys.exit(1)
    return service


def get_task_definition(ecs, td_name):
    try:
        res = ecs.describe_task_definition(taskDefinition=td_name)
    except ClientError as e:
        click.echo(e.response['Error']['Message'], err=True)
        sys.exit(1)
    return res['taskDefinition']

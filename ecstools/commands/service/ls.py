import click
import sys

from botocore.exceptions import ClientError


@click.command()
@click.argument('cluster')
@click.option('-A', '--arn', is_flag=True, help='Show ARN')
@click.pass_context
def cli(ctx, cluster, arn):
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

    for s in services:
        click.echo('%s' % s)

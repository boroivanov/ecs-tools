import click
import sys

from botocore.exceptions import ClientError

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
    try:
        ecs.update_service(
            cluster=cluster,
            service=service,
            desiredCount=count
        )
    except ClientError as e:
        click.echo(e.response['Error']['Message'], err=True)
        sys.exit(1)

    utils.monitor_deployment(ecs, elbv2, cluster, service)

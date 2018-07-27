import sys
import click

import ecstools.lib.utils as utils
from ecstools.lib.config import config


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.option('-g', '--group', is_flag=True, help='Monitor service group')
@click.option('-e', '--exit-on-complete', is_flag=True, help='Exit when all'
              ' deployments are completed')
@click.pass_context
def top(ctx, cluster, service, group, exit_on_complete):
    """Monitor service"""
    ecs = ctx.obj['ecs']
    elbv2 = ctx.obj['elbv2']

    try:
        if group:
            if service in config['service-group']:
                service = config['service-group'][service].split(' ')
            else:
                click.echo('Error: Service group not in config file.')
                sys.exit(1)
    except KeyError:
        click.echo('Error: Section "service-config" not in config file.')
        sys.exit(1)

    utils.monitor_deployment(ecs, elbv2, cluster, service,
                             exit_on_complete=exit_on_complete)

import click
import sys

from botocore.exceptions import ClientError

import ecstools.lib.utils as utils


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.pass_context
def cli(ctx, cluster, service):
    """Describe service"""
    ecs = ctx.obj['ecs']
    elbv2 = ctx.obj['elbv2']

    s = utils.describe_services(ecs, cluster, service)

    # Print Service Info
    cls_name = s['clusterArn'].split('/')[-1]
    def_name = s['taskDefinition'].split('/')[-1]
    general_info = (cls_name, s['serviceName'], def_name, s['launchType'])
    counts = (s['desiredCount'], s['runningCount'], s['pendingCount'])

    click.secho('%s %s %s %s' % (general_info), fg='blue')
    click.secho(('Desired: %s Running: %s Pending: %s' %
                 (counts)), fg='white')

    td = utils.describe_task_definition(ecs, s['taskDefinition'])
    containers = td['containerDefinitions']
    for c in containers:
        click.echo('Container:        %s' % c['image'].split('/')[-1])

    for lb in s['loadBalancers']:
        if 'targetGroupArn' in lb:
            tg_info = utils.describe_target_group_info(elbv2, lb)
            click.echo(
                'Target Group:     {group} {container} {port} {states}'.format(**tg_info))

    nc = s['networkConfiguration']['awsvpcConfiguration']
    click.echo('Subnets:          %s' % ' '.join(nc['subnets']))
    click.echo('Security Groups:  %s' % ' '.join(nc['securityGroups']))
    click.echo('Public IP:        %s' % nc['assignPublicIp'])
    click.echo('Created:          %s' % s['createdAt'].replace(microsecond=0))

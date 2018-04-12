import click
import sys

from botocore.exceptions import ClientError


@click.command()
@click.argument('cluster')
@click.argument('service')
@click.pass_context
def cli(ctx, cluster, service):
    """Describe service"""
    ecs = ctx.obj['ecs']
    elbv2 = ctx.obj['elbv2']

    try:
        response = ecs.describe_services(
            cluster=cluster,
            services=[service]
        )
        s = response['services'][0]
    except ClientError as e:
        if e.response['Error']['Code'] == 'ClusterNotFoundException':
            click.echo('Cluster not found.', err=True)
        else:
            click.echo(e, err=True)
        sys.exit(1)
    except:
        click.echo('Service not found.', err=True)
        sys.exit(1)

    # Print Service Info
    cls_name = s['clusterArn'].split('/')[-1]
    def_name = s['taskDefinition'].split('/')[-1]
    general_info = (cls_name, s['serviceName'], def_name, s['launchType'])
    counts = (s['desiredCount'], s['runningCount'], s['pendingCount'])

    click.secho('%s %s %s %s' % (general_info), fg='blue')
    click.secho(('Desired: %s Running: %s Pending: %s' %
                 (counts)), fg='white')

    td = get_task_definition(ecs, s['taskDefinition'])
    containers = td['containerDefinitions']
    for c in containers:
        click.echo('Container:        %s' % c['image'].split('/')[-1])

    for lb in s['loadBalancers']:
        tgs_state = {}
        if 'loadBalancerName' in lb:
            click.echo('LoadBalancer: %s' % lb['loadBalancerName'])
        if 'targetGroupArn' in lb:
            click.echo('Target Group:     %s' %
                       lb['targetGroupArn'].split('/')[-2], nl=False)
            targets = elbv2.describe_target_health(
                TargetGroupArn=lb['targetGroupArn'])

            for t in targets['TargetHealthDescriptions']:
                state = t['TargetHealth']['State']
                if state in tgs_state:
                    tgs_state[state] += 1
                else:
                    tgs_state[state] = 1
        click.echo('  %s' % lb['containerName'], nl=False)
        click.echo(' %s' % lb['containerPort'], nl=False)
        if tgs_state:
            states = ' '.join(['{}: {}'.format(k, v)
                               for k, v in tgs_state.items()])
            click.echo('  %s' % states)
        else:
            click.echo()

    nc = s['networkConfiguration']['awsvpcConfiguration']
    click.echo('Subnets:          %s' % " ".join(nc['subnets']))
    click.echo('Security Groups:  %s' % " ".join(nc['securityGroups']))
    click.echo('Public IP:        %s' % nc['assignPublicIp'])
    click.echo('Created:          %s' % s['createdAt'].replace(microsecond=0))


def get_task_definition(ecs, td_name):
    try:
        res = ecs.describe_task_definition(taskDefinition=td_name)
    except ClientError as e:
        click.echo(e.response['Error']['Message'], err=True)
        sys.exit(1)
    return res['taskDefinition']

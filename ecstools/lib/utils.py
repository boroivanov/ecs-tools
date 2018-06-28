import click
import time
import sys

from botocore.exceptions import ClientError

from reprint import output

idx = 0


def index():
    global idx
    idx += 1
    return idx


def monitor_deployment(ecs, elbv2, cluster, service):
    # Reprint service and deployments info
    with output(initial_len=20, interval=0) as out:
        while True:
            s = describe_services(ecs, cluster, service)

            global idx
            idx = 0

            cls_name = s['clusterArn'].split('/')[-1]
            srv_name = s['serviceName']
            out[idx] = '{} {} deployments:'.format(cls_name, srv_name)
            out[index()] = '\n'

            print_deployment_info(idx, out, ecs, s['deployments'])
            out[index()] = '\n'
            print_loadbalancer_into(idx, out, elbv2, s['loadBalancers'])
            print_ecs_events(idx, out, s['events'][:2])

            time.sleep(2)


def print_deployment_info(idx, out, ecs, deployments):
    for d in deployments:
        d_info = (
            d['status'],
            d['taskDefinition'].split('/')[-1],
            d['desiredCount'],
            d['runningCount'],
            d['pendingCount']
        )
        idx += deployments.index(d)
        out[index()] = '{:<8} {}  desired: {} running: {} ' \
            'pending: {}'.format(
            *d_info)

        # Print Container Information
        td = describe_task_definition(ecs, d['taskDefinition'])
        containers = td['containerDefinitions']
        for c in containers:
            out[index()] = '{} - {}'.format(
                ' ' * 8,
                c['image'].split('/')[-1]
            )
    out[index()] = '\n'


def print_loadbalancer_into(idx, out, elbv2, loadBalancers):
    for lb in loadBalancers:
        if 'targetGroupArn' in lb:
            tg_info = describe_target_group_info(elbv2, lb)
            out[index()] = 'Target Group: {group}  ' \
                '{container} {port} {states}'.format(
                **tg_info)
    out[index()] = '\n'


def print_ecs_events(idx, out, events):
    for e in events:
        idx += events.index(e)
        createdAt = e['createdAt'].replace(microsecond=0)
        out[index()] = '{} {}'.format(createdAt, e['message'])


def describe_target_group_info(elbv2, lb):
    targets = elbv2.describe_target_health(TargetGroupArn=lb['targetGroupArn'])

    states = target_health_states(targets['TargetHealthDescriptions'])

    summary = {
        'group': lb['targetGroupArn'].split('/')[-2],
        'container': lb['containerName'],
        'port': lb['containerPort'],
        'states': ' '.join(['{}: {}'.format(k, v) for k, v in states.items()])
    }
    return summary


def target_health_states(target_health_descriptions):
    states = {}
    for t in target_health_descriptions:
        state = t['TargetHealth']['State']
        if state in states:
            states[state] += 1
        else:
            states[state] = 1
    return states


def describe_task_definition(ecs, td_name):
    try:
        res = ecs.describe_task_definition(taskDefinition=td_name)
    except ClientError as e:
        click.echo(e.response['Error']['Message'], err=True)
        sys.exit(1)
    return res['taskDefinition']


def describe_services(ecs, cluster, service):
    try:
        response = ecs.describe_services(
            cluster=cluster,
            services=[service]
        )
        return response['services'][0]
    except ClientError as e:
        if e.response['Error']['Code'] == 'ClusterNotFoundException':
            click.echo('Cluster not found.', err=True)
        else:
            click.echo(e, err=True)
        sys.exit(1)
    except IndexError:
        click.echo('Service not found.', err=True)
        sys.exit(1)


def update_service(ecs, **params):
    try:
        ecs.update_service(**params)
    except ClientError as e:
        click.echo(e.response['Error']['Message'], err=True)
        sys.exit(1)


def copy_task_definition(td):
    aws_reserved_params = ['status',
                           'compatibilities',
                           'taskDefinitionArn',
                           'revision',
                           'requiresAttributes'
                           ]
    new_td = td.copy()

    for k in aws_reserved_params:
        del new_td[k]
    return new_td
